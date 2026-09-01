import os
import json
import csv
import io
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
        j_id = j.get("id")
        j_status = statuses.get(j_id, "new")
        annotated_jobs.append({**j, "user_status": j_status})

    if status_filter == "applied":
        annotated_jobs = [j for j in annotated_jobs if j["user_status"] == "applied"]
    elif status_filter == "active":
        annotated_jobs = [j for j in annotated_jobs if j["user_status"] != "dismissed"]

    if scope and scope.lower() == "local":
        annotated_jobs = [j for j in annotated_jobs if j.get("scope") == "local" or 'częstochowa' in j["location"].lower() or 'czestochowa' in j["location"].lower()]
    elif scope and scope.lower() == "country":
        annotated_jobs = [j for j in annotated_jobs if j.get("scope") == "country" or ('częstochowa' not in j["location"].lower() and 'czestochowa' not in j["location"].lower())]

    if work_mode and work_mode.lower() != "all":
        annotated_jobs = [j for j in annotated_jobs if j["work_mode"].lower() == work_mode.lower()]

    return {"count": len(annotated_jobs), "jobs": annotated_jobs}

@app.post("/api/jobs/{job_id}/status")
def update_status(job_id: str, payload: StatusUpdateRequest):
    """Update tracking status of a job (viewed, applied, dismissed)."""
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    set_job_status(job_id, payload.status, target_job)
    return {"status": "ok", "job_id": job_id, "new_status": payload.status}

@app.get("/api/jobs/{job_id}/cover-letter")
def get_cover_letter(job_id: str, lang: Optional[str] = "pl"):
    """Generate a full, un-truncated cover letter on demand."""
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    
    if not target_job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = get_candidate_profile()
    full_letter = generate_full_cover_letter(target_job, profile, lang=lang)
    return {"job_id": job_id, "lang": lang, "cover_letter": full_letter}

@app.post("/api/jobs/extend-search")
def extend_search():
    """Perform an extended search for more live jobs."""
    try:
        updated_jobs = refresh_ranked_jobs(force_live_fetch=True)
        return {"status": "ok", "count": len(updated_jobs), "jobs": updated_jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-package/{job_id}")
def download_package(job_id: str, include_cv: bool = Query(True), lang: str = Query("pl")):
    """Generate and download ZIP application package (.docx + .pdf + Candidate CV)."""
    jobs = load_cached_ranked_jobs()
    target_job = next((j for j in jobs if j.get("id") == job_id), None)
    
    if not target_job:
        raise HTTPException(status_code=404, detail="Job offer not found")

    profile = get_candidate_profile()
    # Generate full, complete cover letter on demand!
    cover_text = generate_full_cover_letter(target_job, profile, lang=lang)

    zip_bytes = build_application_zip(target_job, cover_text, include_cv=include_cv)
    
    company_name = target_job.get("company", "Job").replace(" ", "_")
    filename = f"ApplicationPackage_{company_name}.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/export-csv")
def export_csv():
    """Export applied jobs history to CSV."""
    history = get_applied_history()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Job ID", "Job Title", "Company", "Location", "Date Applied", "Link"])
    
    for item in history:
        writer.writerow([
            item.get("job_id"),
            item.get("title"),
            item.get("company"),
            item.get("location"),
            item.get("applied_at"),
            item.get("apply_url")
        ])
        
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applied_jobs_history.csv"}
    )

@app.post("/api/generate-blurb")
def generate_blurb(job_req: CustomJobRequest):
    """Evaluate custom job description on demand."""
    try:
        profile = get_candidate_profile()
        job_dict = {
            "title": job_req.title,
            "company": job_req.company,
            "location": job_req.location,
            "work_mode": job_req.work_mode,
            "description": job_req.description
        }
        match_result = evaluate_job_match(job_dict, profile)
        full_cover = generate_full_cover_letter(job_dict, profile, lang="pl")
        match_result["cover_blurb"] = {"pl": full_cover, "en": full_cover}
        return {"job": job_dict, "match": match_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=True)
