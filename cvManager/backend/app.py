import os
import json
import csv
import io
import requests
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Response, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.cv_parser import get_candidate_profile
from backend.job_fetcher import fetch_jobs, fetch_live_linkedin_jobs
from backend.ai_matcher import rank_all_jobs, evaluate_job_match, generate_full_cover_letter
from backend.storage import set_job_status, get_job_statuses, get_applied_history
from backend.package_builder import build_application_zip

RANKED_CACHE_FILE = "ranked_jobs_cache.json"
LAST_SEARCH_FILE = "last_search_info.json"

app = FastAPI(title="cvManager - AI Job Matcher & Application Package Builder", version="3.0.0")

# Setup static files and templates
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

CACHED_RANKED_JOBS: List[Dict[str, Any]] = []

class CustomJobRequest(BaseModel):
    title: str
    company: str
    location: str
    work_mode: str
    description: str

class StatusUpdateRequest(BaseModel):
    status: str  # "viewed", "applied", "dismissed"

def get_last_search_info() -> Dict[str, Any]:
    if os.path.exists(LAST_SEARCH_FILE):
        try:
            with open(LAST_SEARCH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_searched": None}

def update_search_timestamp() -> Dict[str, Any]:
    info = {"last_searched": datetime.now().isoformat()}
    with open(LAST_SEARCH_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    return info

def load_cached_ranked_jobs() -> List[Dict[str, Any]]:
    global CACHED_RANKED_JOBS
    if os.path.exists(RANKED_CACHE_FILE):
        try:
            with open(RANKED_CACHE_FILE, "r", encoding="utf-8") as f:
                CACHED_RANKED_JOBS = json.load(f)
                return CACHED_RANKED_JOBS
        except Exception:
            pass
    return []

def refresh_ranked_jobs(force_live_fetch: bool = False) -> List[Dict[str, Any]]:
    global CACHED_RANKED_JOBS
    if force_live_fetch:
        raw_jobs = fetch_live_linkedin_jobs(limit_per_query=3)
    else:
        raw_jobs = fetch_jobs(scope="all", work_mode="all")
        
    profile = get_candidate_profile()
    CACHED_RANKED_JOBS = rank_all_jobs(raw_jobs, profile)
    with open(RANKED_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(CACHED_RANKED_JOBS, f, ensure_ascii=False, indent=2)
    update_search_timestamp()
    return CACHED_RANKED_JOBS

@app.on_event("startup")
def startup_event():
    """Load cached ranked jobs on startup."""
    jobs = load_cached_ranked_jobs()
    if not jobs:
        print("Pre-warming ranked jobs cache...")
        refresh_ranked_jobs()

@app.get("/")
def read_root(request: Request):
    """Render the dashboard UI."""
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/profile")
def get_profile():
    """Get parsed candidate profile."""
    try:
        profile = get_candidate_profile()
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search-status")
def search_status():
    """Get info on when extended search was last run."""
    return get_last_search_info()

@app.get("/api/jobs")
def get_ranked_jobs(scope: Optional[str] = "all", work_mode: Optional[str] = "all", status_filter: Optional[str] = "active", refresh: bool = False):
    """Get jobs ranked by Gemini match score with tracking status."""
    global CACHED_RANKED_JOBS
    
    if refresh or not CACHED_RANKED_JOBS:
        CACHED_RANKED_JOBS = load_cached_ranked_jobs()
        if refresh or not CACHED_RANKED_JOBS:
            CACHED_RANKED_JOBS = refresh_ranked_jobs(force_live_fetch=refresh)
        
    jobs = CACHED_RANKED_JOBS
    statuses = get_job_statuses()

    annotated_jobs = []
    for j in jobs:
        st = statuses.get(j["id"], "new")
        user_st = st if isinstance(st, str) else (st.get("status", "new") if isinstance(st, dict) else "new")
        
        if status_filter == "applied" and user_st != "applied":
            continue
        if status_filter == "active" and user_st in ["dismissed"]:
            continue
        if status_filter == "dismissed" and user_st != "dismissed":
            continue
            
        if scope != "all" and j.get("scope") != scope:
            continue
        if work_mode != "all" and j.get("work_mode") != work_mode:
            continue
            
        j_copy = dict(j)
        j_copy["user_status"] = user_st
        annotated_jobs.append(j_copy)

    return {"count": len(annotated_jobs), "jobs": annotated_jobs}

@app.post("/api/jobs/{job_id}/status")
def update_job_status(job_id: str, payload: StatusUpdateRequest):
    """Update job tracking status (applied, dismissed, etc)."""
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    set_job_status(job_id, payload.status, target_job)
    return {"status": "ok", "job_id": job_id, "new_status": payload.status}

@app.get("/api/jobs/{job_id}/verify")
def verify_job_availability(job_id: str):
    """Check if a job offer link is active or expired."""
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    url = target_job.get("apply_url") or target_job.get("url")
    if not url or url == "#" or "linkedin.com/jobs/search" in url:
        return {"job_id": job_id, "active": True, "status": "Search Query Link"}

    try:
        res = requests.head(url, timeout=5, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        is_ok = (res.status_code < 400)
        return {"job_id": job_id, "active": is_ok, "status_code": res.status_code}
    except Exception:
        return {"job_id": job_id, "active": False, "status_code": 500}

@app.get("/api/jobs/{job_id}/cover-letter")
def get_cover_letter(job_id: str, lang: Optional[str] = "pl", force: bool = False):
    """Generate or retrieve stored cover letter from database/cache."""
    global CACHED_RANKED_JOBS
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    saved = target_job.get("saved_cover_letters", {})
    if not force and lang in saved and saved[lang]:
        return {"job_id": job_id, "lang": lang, "cover_letter": saved[lang], "cached": True}

    profile = get_candidate_profile()
    full_letter = generate_full_cover_letter(target_job, profile, lang=lang)
    
    # Store in memory & cache file
    if "saved_cover_letters" not in target_job:
        target_job["saved_cover_letters"] = {}
    target_job["saved_cover_letters"][lang] = full_letter

    with open(RANKED_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(CACHED_RANKED_JOBS, f, ensure_ascii=False, indent=2)

    return {"job_id": job_id, "lang": lang, "cover_letter": full_letter, "cached": False}

@app.post("/api/jobs/extend-search")
def extend_search():
    """Perform an extended search for more live jobs."""
    try:
        updated_jobs = refresh_ranked_jobs(force_live_fetch=True)
        search_info = get_last_search_info()
        return {"status": "ok", "count": len(updated_jobs), "jobs": updated_jobs, "last_searched": search_info["last_searched"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-blurb")
def generate_custom_blurb(payload: CustomJobRequest):
    """Generate AI blurb for a custom user-submitted job."""
    profile = get_candidate_profile()
    job_dict = payload.dict()
    eval_result = evaluate_job_match(job_dict, profile)
    return {"status": "ok", "match": eval_result}

@app.get("/api/download-package/{job_id}")
def download_package(job_id: str, include_cv: bool = True, lang: Optional[str] = "pl"):
    """Generate and stream the .ZIP application package."""
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Ensure cover letter exists in cache
    saved = target_job.get("saved_cover_letters", {})
    if lang in saved and saved[lang]:
        cover_letter = saved[lang]
    else:
        profile = get_candidate_profile()
        cover_letter = generate_full_cover_letter(target_job, profile, lang=lang)
        if "saved_cover_letters" not in target_job:
            target_job["saved_cover_letters"] = {}
        target_job["saved_cover_letters"][lang] = cover_letter
        with open(RANKED_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(CACHED_RANKED_JOBS, f, ensure_ascii=False, indent=2)

    profile = get_candidate_profile()
    zip_bytes = build_application_zip(target_job, profile, cover_letter, include_cv=include_cv, lang=lang)
    
    filename = f"Application_Package_{target_job.get('company','Job')}.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export-csv")
def export_csv():
    """Export tracked jobs to CSV."""
    applied = get_applied_history()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Job ID", "Title", "Company", "Location", "Match Score", "Status", "Timestamp"])
    for item in applied:
        job = item.get("job_data", {})
        writer.writerow([
            item.get("job_id"),
            job.get("title", "N/A"),
            job.get("company", "N/A"),
            job.get("location", "N/A"),
            job.get("match", {}).get("match_score", "N/A"),
            item.get("status"),
            item.get("timestamp")
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cvManager_Applied_Jobs.csv"}
    )
