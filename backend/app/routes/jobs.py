import json
import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Query, Request
from backend.app.config import BASE_DIR

router = APIRouter(tags=["Opportunities"])

_cached_opportunities = None


def get_opportunities():
    global _cached_opportunities
    json_path = BASE_DIR / "aggregated_opportunities.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                _cached_opportunities = json.load(f)
                return _cached_opportunities
        except Exception as e:
            print(f"Notice reading aggregated_opportunities.json: {e}")
    return _cached_opportunities or []


@router.get("/api/jobs")
@router.get("/api/opportunities/search")
def get_jobs(
    prompt: str = "",
    q: str = "",
    category: str = "all",
    page: int = 1,
    limit: int = 12
):
    query_str = (prompt or q or "").strip().lower()
    cat_str = (category or "all").strip().lower()

    all_items = get_opportunities()

    filtered = []
    for item in all_items:
        # Category check
        item_cat = str(item.get("category") or "").strip().lower()
        item_type = str(item.get("type") or "").strip().lower()

        if cat_str != "all":
            if cat_str in ("hackathons", "hackathon") and "hackathon" not in item_cat and "hackathon" not in item_type:
                continue
            elif cat_str in ("internships", "internship") and "internship" not in item_cat and "internship" not in item_type:
                continue
            elif cat_str not in ("hackathons", "hackathon", "internships", "internship") and cat_str not in item_cat:
                continue

        # Query search check
        if query_str:
            title = str(item.get("title") or "").lower()
            company = str(item.get("company") or item.get("organization") or "").lower()
            desc = str(item.get("description") or "").lower()
            skills = " ".join([str(s).lower() for s in item.get("skills_required", [])])
            if query_str not in title and query_str not in company and query_str not in desc and query_str not in skills:
                continue

        filtered.append(item)

    total = len(filtered)
    start = max(0, (page - 1) * limit)
    end = start + limit
    paginated = filtered[start:end]

    return {
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "jobs": paginated,
        "items": paginated
    }


@router.post("/api/applications/apply")
def apply_job(req: dict):
    return {
        "success": True,
        "message": "Application submitted successfully.",
        "applicationId": f"app_{int(os.times().system * 1000)}"
    }


@router.get("/api/applications/status")
def application_status(jobId: Optional[str] = None):
    return {
        "success": True,
        "applied": False,
        "status": "Not Applied"
    }
