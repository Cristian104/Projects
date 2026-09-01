import os
import json
from typing import Dict, Any, List

TRACKER_FILE = "job_tracker_data.json"

def load_tracker_data() -> Dict[str, Any]:
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"jobs_status": {}, "applied_history": []}

def save_tracker_data(data: Dict[str, Any]):
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def set_job_status(job_id: str, status: str, job_data: Dict[str, Any] = None):
    data = load_tracker_data()
    data["jobs_status"][job_id] = status
    if status == "applied" and job_data:
        # Save to applied history
        history_item = {
            "job_id": job_id,
            "title": job_data.get("title"),
            "company": job_data.get("company"),
            "location": job_data.get("location"),
            "apply_url": job_data.get("apply_url"),
            "applied_at": os.popen("date /t").read().strip() or "Today"
        }
        data["applied_history"].append(history_item)
    save_tracker_data(data)

def get_job_statuses() -> Dict[str, str]:
    data = load_tracker_data()
    return data.get("jobs_status", {})

def get_applied_history() -> List[Dict[str, Any]]:
    data = load_tracker_data()
    return data.get("applied_history", [])
