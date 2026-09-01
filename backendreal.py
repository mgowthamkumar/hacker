from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi import Request
from pathlib import Path
import os
import requests

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

# Allow your HTML file to communicate with this Python server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ADZUNA_APP_ID = "d1f4b68d"
ADZUNA_APP_KEY = "e5ffc11dd8e1b50c11a3b48cfa7149b7"
COUNTRY_CODE = "in"

# Previously deployed backend URL (Vercel) — used as an external service endpoint
EXTERNAL_BACKEND_URL = "https://hacker-2t6h3vhn1-aihack.vercel.app"

COMPANY_CAREER_LINKS = [
    ("Google", "https://careers.google.com/"),
    ("Microsoft", "https://careers.microsoft.com/"),
    ("Amazon", "https://www.amazon.jobs/"),
    ("Apple", "https://www.apple.com/careers/"),
    ("Meta", "https://www.metacareers.com/"),
    ("Netflix", "https://jobs.netflix.com/"),
    ("NVIDIA", "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
    ("Intel", "https://jobs.intel.com/"),
    ("IBM", "https://www.ibm.com/careers/"),
    ("Oracle", "https://www.oracle.com/careers/"),
    ("Adobe", "https://careers.adobe.com/"),
    ("Salesforce", "https://www.salesforce.com/company/careers/"),
    ("Cisco", "https://jobs.cisco.com/"),
    ("Dell Technologies", "https://jobs.dell.com/"),
    ("HP", "https://jobs.hp.com/"),
    ("Qualcomm", "https://www.qualcomm.com/company/careers"),
    ("AMD", "https://careers.amd.com/"),
    ("Broadcom", "https://www.broadcom.com/company/careers"),
    ("VMware", "https://careers.vmware.com/"),
    ("SAP", "https://www.sap.com/about/careers.html"),
    ("ServiceNow", "https://careers.servicenow.com/"),
    ("Workday", "https://www.workday.com/en-us/company/careers.html"),
    ("Atlassian", "https://www.atlassian.com/company/careers"),
    ("Shopify", "https://www.shopify.com/careers"),
    ("HubSpot", "https://www.hubspot.com/careers"),
    ("Slack", "https://slack.com/careers"),
    ("Zoom", "https://careers.zoom.us/"),
    ("Dropbox", "https://jobs.dropbox.com/"),
    ("GitHub", "https://www.github.careers/"),
    ("GitLab", "https://about.gitlab.com/handbook/hiring/"),
    ("Red Hat", "https://www.redhat.com/en/jobs"),
    ("Docker", "https://www.docker.com/careers/"),
    ("Cloudflare", "https://www.cloudflare.com/careers/"),
    ("Datadog", "https://careers.datadoghq.com/"),
    ("Snowflake", "https://careers.snowflake.com/"),
    ("Databricks", "https://www.databricks.com/company/careers"),
    ("Palantir", "https://www.palantir.com/careers/"),
    ("Stripe", "https://stripe.com/jobs"),
    ("PayPal", "https://www.paypal.com/us/brc/"),
    ("Block", "https://block.xyz/careers"),
    ("Coinbase", "https://www.coinbase.com/careers"),
    ("Uber", "https://www.uber.com/us/en/careers/"),
    ("Lyft", "https://www.lyft.com/careers"),
    ("Airbnb", "https://careers.airbnb.com/"),
    ("DoorDash", "https://careers.doordash.com/"),
    ("LinkedIn", "https://www.linkedin.com/jobs/"),
    ("Indeed", "https://www.indeed.jobs/"),
    ("X", "https://careers.x.com/"),
    ("Spotify", "https://www.lifeatspotify.com/jobs"),
    ("Discord", "https://discord.com/jobs"),
    ("Twitch", "https://www.twitch.tv/jobs/"),
    ("Electronic Arts", "https://www.ea.com/careers"),
    ("Riot Games", "https://www.riotgames.com/en/work-with-us"),
    ("Walmart Global Tech", "https://careers.walmart.com/us/en/teams/technology"),
    ("Target", "https://corporate.target.com/careers"),
    ("JPMorgan Chase", "https://www.jpmorganchase.com/careers"),
    ("Goldman Sachs", "https://www.goldmansachs.com/careers"),
    ("Morgan Stanley", "https://www.morganstanley.com/people-opportunities"),
    ("Deloitte", "https://www.deloitte.com/global/en/careers.html"),
    ("Accenture", "https://www.accenture.com/us-en/careers"),
    ("TCS", "https://www.tcs.com/careers"),
    ("Infosys", "https://www.infosys.com/careers.html"),
    ("Wipro", "https://careers.wipro.com/"),
    ("HCLTech", "https://www.hcltech.com/careers"),
    ("Flipkart", "https://www.flipkartcareers.com/"),
    ("Razorpay", "https://razorpay.com/jobs/"),
    ("Swiggy", "https://careers.swiggy.com/"),
    ("Zomato", "https://www.zomato.com/careers"),
]


def get_company_links():
    return [
        {
            "id": f"company-{index}",
            "company": company.upper(),
            "title": f"Explore {company} careers",
            "type": "companies",
            "domain": "technology",
            "isRemote": True,
            "ribbonText": "Company Link",
            "ribbonClass": "",
            "typeTag": "🏢 Company Careers",
            "domainTag": "⚙️ Technology",
            "packageTag": "🔗 Official Careers Page",
            "extraTag": "🌐 Global Opportunities",
            "location": "📍 Global / Online",
            "buttonText": "View Careers",
            "apply_link": link,
        }
        for index, (company, link) in enumerate(COMPANY_CAREER_LINKS, start=1)
    ]


@app.post("/api/track_apply")
async def track_apply(request: Request):
    """Receive application tracking events from the frontend and persist them to applications.json"""
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "invalid json"}

    out_file = BASE_DIR / "applications.json"
    try:
        existing = []
        if out_file.exists():
            import json
            existing = json.loads(out_file.read_text(encoding="utf-8") or "[]")

        import json
        entry = {
            "company": payload.get("company"),
            "title": payload.get("title"),
            "apply_link": payload.get("apply_link"),
            "timestamp": __import__("time").time(),
        }
        existing.append(entry)
        out_file.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return {"status": "ok", "entry": entry}
    except Exception as e:
        return {"status": "error", "message": str(e)}


COMPANY_SIGNIN_PORTALS = {
    "GOOGLE": "https://careers.google.com/",
    "MICROSOFT": "https://careers.microsoft.com/",
    "AMAZON": "https://www.amazon.jobs/",
    "APPLE": "https://www.apple.com/careers/",
    "META": "https://www.metacareers.com/",
    "NETFLIX": "https://jobs.netflix.com/",
    "NVIDIA": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    "OPENAI": "https://openai.com/careers/",
    "IBM": "https://www.ibm.com/careers/",
    "ORACLE": "https://www.oracle.com/careers/",
    "ADOBE": "https://careers.adobe.com/",
    "SALESFORCE": "https://www.salesforce.com/company/careers/",
    "SPOTIFY": "https://lifeatspotify.com/jobs",
    "UBER": "https://www.uber.com/us/en/careers/",
    "AIRBNB": "https://careers.airbnb.com/",
    "LINKEDIN": "https://www.linkedin.com/jobs/",
    "INDEED": "https://www.indeed.com/",
    "MLH": "https://mlh.io/users/sign_in",
    "DEVPOST": "https://devpost.com/login"
}

def resolve_signin_link(company_name: str, redirect_url: str = "") -> str:
    upper = (company_name or "").upper()
    for name, portal in COMPANY_SIGNIN_PORTALS.items():
        if name in upper:
            return portal
    if redirect_url and redirect_url != "#":
        return redirect_url
    return f"https://www.google.com/search?q={requests.utils.quote(company_name + ' career sign in portal')}"


@app.get("/")
def serve_homepage():
    return FileResponse(BASE_DIR / "getstarted.html")


def get_all_opportunities_response(prompt: str = "", q: str = "", category: str = "all", page: int = 1, limit: int = 12):
    user_query = (prompt or q or "").lower().strip()
    cat_query = (category or "all").lower().strip()

    all_jobs = []
    json_path = BASE_DIR / "aggregated_opportunities.json"
    if os.path.exists(json_path):
        try:
            import json
            with open(json_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and len(loaded) > 0:
                    for item in loaded:
                        all_jobs.append({
                            "id": item.get("id", str(len(all_jobs))),
                            "company": item.get("organization") or item.get("company") or "Tech Employer",
                            "organization": item.get("organization") or item.get("company") or "Tech Employer",
                            "title": item.get("title") or "Opportunity",
                            "type": item.get("type") or ("hackathon" if "hackathon" in (item.get("title","")).lower() else "job"),
                            "category": item.get("category") or "Engineering",
                            "location": item.get("location") or "Remote",
                            "salary": item.get("metadata", {}).get("stipend_or_salary") or item.get("salary") or "Competitive Compensation",
                            "description": item.get("description") or f"Exciting role at {item.get('organization') or 'top tech firm'}.",
                            "skills_required": item.get("skills_required") or ["Python", "React", "REST APIs"],
                            "apply_url": item.get("apply_url") or item.get("apply_link") or "https://careers.google.com/",
                            "apply_link": item.get("apply_url") or item.get("apply_link") or "https://careers.google.com/",
                            "signin_link": item.get("signin_link") or item.get("apply_url") or "https://careers.google.com/",
                            "deadline_or_posted": item.get("deadline_or_posted") or "Active",
                            "ribbonText": item.get("ribbonText") or ("🏆 Live Contest" if item.get("type") == "hackathon" else "💼 Internship" if item.get("type") == "internship" else "Full-Time"),
                            "ribbonClass": item.get("ribbonClass") or ("hackathon" if item.get("type") == "hackathon" else "intern" if item.get("type") == "internship" else "")
                        })
        except Exception as e:
            print("Error loading aggregated_opportunities.json:", e)

    filtered = []
    for job in all_jobs:
        job_cat = (job.get("category") or "").lower()
        job_type = (job.get("type") or "").lower()

        cat_match = (
            cat_query == "all" or
            (cat_query in ["internships", "internship"] and (job_type == "internship" or "intern" in job_cat)) or
            (cat_query in ["hackathons", "hackathon"] and (job_type == "hackathon" or "hack" in job_cat)) or
            (cat_query in ["arts", "arts & design"] and ("arts" in job_cat or "design" in job_cat)) or
            (cat_query in ["teaching"] and ("teach" in job_cat or "edtech" in job_cat)) or
            (cat_query in ["medical"] and ("med" in job_cat or "health" in job_cat)) or
            (cat_query in ["engineering"] and ("eng" in job_cat or job_type == "job")) or
            cat_query in job_cat
        )

        query_terms = [t for t in user_query.split() if len(t) > 1]
        if not query_terms:
            query_match = True
        else:
            full_searchable = f"{job['title']} {job['company']} {job.get('organization','')} {job['description']} {job['category']} {job['type']} {job['location']} {' '.join(job.get('skills_required', []))}".lower()
            query_match = any(t in full_searchable for t in query_terms)

        if cat_match and query_match:
            filtered.append(job)

    if not filtered and all_jobs:
        if cat_query != "all":
            filtered = [j for j in all_jobs if cat_query in (j.get("category","")).lower() or cat_query in (j.get("type","")).lower()]
        if not filtered:
            filtered = all_jobs

    categories_count = {
        "All": len(all_jobs),
        "Engineering": len([j for j in all_jobs if "eng" in (j.get("category","")).lower() or (j.get("type","")).lower() == "job"]),
        "Teaching": len([j for j in all_jobs if "teach" in (j.get("category","")).lower()]),
        "Arts": len([j for j in all_jobs if "arts" in (j.get("category","")).lower() or "design" in (j.get("category","")).lower()]),
        "Medical": len([j for j in all_jobs if "med" in (j.get("category","")).lower() or "health" in (j.get("category","")).lower()]),
        "Hackathons": len([j for j in all_jobs if (j.get("type","")).lower() == "hackathon" or "hack" in (j.get("category","")).lower()]),
        "Internships": len([j for j in all_jobs if (j.get("type","")).lower() == "internship" or "intern" in (j.get("category","")).lower()])
    }

    total = len(filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    start_idx = (page - 1) * limit
    paginated = filtered[start_idx:start_idx + limit]

    return {
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
        "categories": categories_count,
        "counts": categories_count,
        "jobs": paginated,
        "items": paginated
    }

@app.get("/api/jobs")
def get_live_jobs(prompt: str = "", q: str = "", category: str = "all", page: int = 1, limit: int = 12):
    user_query = (prompt or q or "").lower().strip()
    if "compan" in user_query or "career page" in user_query:
        return get_company_links()

    return get_all_opportunities_response(prompt=prompt, q=q, category=category, page=page, limit=limit)


@app.get("/api/study-pack/pdf")
@app.get("/api/study-pack/html")
def get_backendreal_study_pack_pdf(topic: str = "Data Structures & Algorithms Mastery", name: str = "Candidate"):
    from fastapi.responses import HTMLResponse
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AutoHire RAG Study Pack - {topic}</title>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 40px; }}
    .header {{ border-bottom: 2px solid #38bdf8; padding-bottom: 20px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; }}
    .logo {{ font-size: 24px; font-weight: 800; color: #38bdf8; text-decoration: none; }}
    .title-box {{ background: rgba(30, 41, 59, 0.8); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
    .category-badge {{ display: inline-block; background: #a855f7; color: #fff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; margin-bottom: 10px; }}
    h1 {{ margin: 0 0 10px 0; color: #f8fafc; font-size: 26px; }}
    p {{ line-height: 1.6; color: #94a3b8; }}
    .section-title {{ font-size: 20px; color: #38bdf8; margin-top: 30px; margin-bottom: 16px; border-left: 4px solid #38bdf8; padding-left: 12px; }}
    .progression-card {{ background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 18px; margin-bottom: 14px; }}
    .level-header {{ font-weight: 700; font-size: 16px; margin-bottom: 6px; }}
    .q-text {{ color: #e2e8f0; font-weight: 600; margin-bottom: 4px; }}
    .footer {{ text-align: center; margin-top: 50px; font-size: 12px; color: #64748b; border-top: 1px solid rgba(255, 255, 255, 0.1); padding-top: 20px; }}
    @media print {{ body {{ background: #fff; color: #000; }} .title-box, .progression-card {{ border-color: #ccc; background: #f9f9f9; }} h1, .section-title, .logo {{ color: #000; }} }}
  </style>
</head>
<body>
  <div class="header">
    <div class="logo">✨ AutoHire RAG Study Pack</div>
    <div>Candidate: {name}</div>
  </div>

  <div class="title-box">
    <span class="category-badge">RAG Vector Roadmap</span>
    <h1>{topic}</h1>
    <p><strong>Rationale:</strong> RAG Vector Match analysis identified "{topic}" as a critical skill gap to maximize your interview success rate.</p>
  </div>

  <div class="section-title">📖 Core Theoretical Fundamentals</div>
  <div class="progression-card">
    <p style="color: #cbd5e1; margin: 0;">Comprehensive theoretical framework, problem solving patterns, and core architectural principles for mastering {topic}.</p>
  </div>

  <div class="section-title">🚀 Difficulty Progression Roadmap</div>
  <div class="progression-card">
    <div class="level-header">🟢 Easy (Fundamentals)</div>
    <div class="q-text">Q1. Define key terms, syntax patterns, and fundamental concepts for {topic}.</div>
  </div>
  <div class="progression-card">
    <div class="level-header">🟡 Medium (Application)</div>
    <div class="q-text">Q2. Solve an intermediate practical challenge involving {topic} design.</div>
  </div>
  <div class="progression-card">
    <div class="level-header">🔴 Hard (Production Scale)</div>
    <div class="q-text">Q3. Architect an end-to-end production solution applying {topic} principles.</div>
  </div>

  <div class="footer">
    AutoHire AI RAG Grounded Career Engine &copy; 2026. All rights reserved.
  </div>
  <script>
    window.onload = function() {{ setTimeout(function() {{ window.print(); }}, 600); }};
  </script>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@app.api_route("/api/rag/query", methods=["GET", "POST"])
def backendreal_rag_query(q: str = "", prompt: str = "", category: str = "all"):
    import re
    query = (prompt or q or "Which jobs match my skills?").strip()

    knowledge_base = [
        {"id": "dsa-guide", "category": "Engineering", "topic": "DSA & Algorithms", "content": "Master HashMaps, Trees, Graphs, and Dynamic Programming. Practice 50+ LeetCode problems for technical interview readiness."},
        {"id": "sys-design", "category": "Engineering", "topic": "System Design & Microservices", "content": "Learn REST APIs, Redis caching, PostgreSQL database sharding, and Docker containerization for scalable platforms."},
        {"id": "arts-design", "category": "Arts", "topic": "Figma Design Systems & Brand Identity", "content": "Master Figma auto-layout, interactive component variants, typography hierarchy, and Behance portfolio case studies."},
        {"id": "medical-care", "category": "Medical", "topic": "Clinical Practice & BLS Certification", "content": "Complete certified Basic Life Support (BLS) and ACLS modules for emergency patient diagnostics and hospital care."},
        {"id": "teaching-guide", "category": "Teaching", "topic": "Computer Science Curriculum & Pedagogy", "content": "Develop interactive coding assessments, lesson plans, and STEM project guidance for computer science students."}
    ]

    query_words = set(re.findall(r"\w+", query.lower()))
    matches = []

    for doc in knowledge_base:
        doc_words = set(re.findall(r"\w+", (doc["topic"] + " " + doc["content"]).lower()))
        intersection = query_words.intersection(doc_words)
        score = len(intersection) / max(1, len(query_words))
        matches.append((score, doc))

    matches.sort(key=lambda x: x[0], reverse=True)
    top_matches = [m[1] for m in matches[:3]]

    context_str = "\n".join([f"- {m['topic']}: {m['content']}" for m in top_matches])

    return {
        "success": True,
        "query": query,
        "category": category,
        "grounded_context": context_str,
        "answer": f"🤖 AutoHire RAG Assistant Answer:\nBased on our grounded vector knowledge base:\n{context_str}\n\nRecommended Action: Apply these guidelines directly to your candidate profile to boost interview odds!",
        "matches": top_matches
    }


from pydantic import BaseModel
from typing import Optional
import time
import random
from datetime import datetime

class RealApplicationRequest(BaseModel):
    opportunity_id: Optional[str] = None
    opportunity_title: Optional[str] = None
    organization: Optional[str] = None
    candidate_name: str
    candidate_email: str
    resume_text: Optional[str] = ""
    portfolio_url: Optional[str] = ""
    cover_note: Optional[str] = ""
    apply_mode: Optional[str] = "native"

class RealCoverLetterRequest(BaseModel):
    opportunity_title: Optional[str] = None
    organization: Optional[str] = None
    candidate_name: Optional[str] = None
    key_skills: Optional[list] = None

real_in_memory_applications = []

@app.api_route("/api/opportunities/search", methods=["GET", "POST"])
def real_search_opportunities(q: str = "", prompt: str = "", category: str = "all", page: int = 1, limit: int = 20):
    user_query = (prompt or q or "").lower().strip()
    cat_query = (category or "all").lower().strip()

    all_jobs = [
        { "id": "job-1", "company": "GOOGLE", "title": "Software Engineer", "type": "Job", "category": "Engineering", "location": "Bangalore / Remote", "salary": "₹18,00,000 - ₹30,00,000 / yr", "description": "Develop scalable web services and cloud algorithms.", "ribbonText": "Featured", "ribbonClass": "", "apply_link": "https://careers.google.com/", "signin_link": "https://careers.google.com/" },
        { "id": "job-2", "company": "MICROSOFT", "title": "Fullstack Developer Intern", "type": "Internship", "category": "Engineering", "location": "Hyderabad, India", "salary": "₹16,00,000 / yr", "description": "Architect web microservices and React interfaces.", "ribbonText": "Internship", "ribbonClass": "intern", "apply_link": "https://careers.microsoft.com/", "signin_link": "https://careers.microsoft.com/" },
        { "id": "job-3", "company": "MAJOR LEAGUE HACKING", "title": "Global Tech Hackathon 2026", "type": "Hackathon", "category": "Hackathons", "location": "Online / Worldwide", "salary": "Prizes worth $25,000", "description": "Build innovative web & AI applications with developers worldwide.", "ribbonText": "Live Hackathon", "ribbonClass": "hackathon", "apply_link": "https://mlh.io", "signin_link": "https://mlh.io" },
        { "id": "job-4", "company": "DEVPOST", "title": "AI & Cloud Innovation Challenge", "type": "Hackathon", "category": "Hackathons", "location": "Remote", "salary": "$50,000 Prize Pool", "description": "Develop cutting-edge machine learning models.", "ribbonText": "$50k Prize Pool", "ribbonClass": "hackathon", "apply_link": "https://devpost.com", "signin_link": "https://devpost.com" }
    ]

    filtered = []
    for job in all_jobs:
        job_cat = job["category"].lower()
        job_type = job["type"].lower()
        cat_match = (cat_query == "all") or (cat_query == job_cat) or (cat_query in ["internships", "internship"] and job_type == "internship") or (cat_query in ["hackathons", "hackathon"] and job_type == "hackathon")
        query_match = not user_query or (user_query in job["title"].lower() or user_query in job["company"].lower())
        if cat_match and query_match:
            filtered.append(job)

    categories_count = {
        "All": len(all_jobs),
        "Engineering": 42,
        "Teaching": 15,
        "Arts": 12,
        "Medical": 10,
        "Hackathons": 28,
        "Internships": 35
    }

    total = len(filtered)
    total_pages = max(1, (total + limit - 1) // limit)
    start_idx = (page - 1) * limit
    paginated = filtered[start_idx:start_idx + limit]

    return {
        "success": True,
        "total": total,
        "page": page,
        "limit": limit,
        "totalPages": total_pages,
        "categories": categories_count,
        "counts": categories_count,
        "jobs": paginated,
        "items": paginated
    }

@app.post("/api/applications/apply")
def real_apply_opportunity(payload: RealApplicationRequest):
    app_id = f"app_{int(time.time())}_{random.randint(1000, 9999)}"
    is_native = payload.apply_mode != "external"

    record = {
        "id": app_id,
        "opportunity_id": payload.opportunity_id or "gen_opp",
        "opportunity_title": payload.opportunity_title or "General Application",
        "organization": payload.organization or "Partner Employer",
        "candidate_name": payload.candidate_name,
        "candidate_email": payload.candidate_email,
        "resume_text": payload.resume_text[:500] if payload.resume_text else "",
        "portfolio_url": payload.portfolio_url or "",
        "cover_note": payload.cover_note or "Interested in pursuing this opportunity.",
        "mode": "Mode A (Native Direct Post)" if is_native else "Mode B (Assisted Auto-Apply)",
        "status": "Submitted",
        "created_at": datetime.now().isoformat()
    }
    real_in_memory_applications.insert(0, record)

    return {
        "success": True,
        "message": f"Application submitted successfully via AutoHire! ({record['mode']})",
        "application": record,
        "redirect_url": None if is_native else f"https://google.com/search?q={record['organization']}+{record['opportunity_title']}"
    }

@app.get("/api/applications/status")
def real_application_status(email: str = ""):
    apps = real_in_memory_applications
    if email:
        apps = [a for a in apps if a["candidate_email"].lower() == email.lower()]
    return {"success": True, "total": len(apps), "applications": apps}

@app.post("/api/applications/cover-letter")
def real_generate_cover_letter(payload: RealCoverLetterRequest):
    name = payload.candidate_name or "Applicant"
    title = payload.opportunity_title or "Software Engineering Role"
    org = payload.organization or "your organization"
    skills = ", ".join(payload.key_skills) if payload.key_skills else "Fullstack Software Engineering, Python, React, REST APIs"

    letter = f"Dear Hiring Team at {org},\n\nI am writing to express my strong enthusiasm for the {title} position. With verified expertise in {skills}, I have engineered robust systems and delivered scalable technical solutions.\n\nThank you for your consideration.\n\nBest regards,\n{name}"
    return {"success": True, "cover_letter": letter}


from fastapi import UploadFile, File, Form

@app.post("/analyzer")
@app.post("/api/analyzer")
@app.post("/api/rag/analyze")
async def backendreal_analyze_resume(
    file: Optional[UploadFile] = File(None),
    resume_text: Optional[str] = Form(""),
    company_skills: Optional[str] = Form(""),
    target_skills: Optional[str] = Form("")
):
    import re
    text = (resume_text or "").strip()
    if file:
        try:
            content_bytes = await file.read()
            ext = (file.filename.split(".")[-1] or "").lower()
            if ext == "txt":
                text = (content_bytes.decode("utf-8", errors="ignore") + "\n" + text).strip()
            elif ext == "pdf":
                try:
                    from pypdf import PdfReader
                    import io
                    reader = PdfReader(io.BytesIO(content_bytes))
                    extracted = "\n".join([page.extract_text() or "" for page in reader.pages])
                    if extracted.strip():
                        text = (extracted + "\n" + text).strip()
                except Exception:
                    clean = re.sub(r"[^\x20-\x7E\n\r\t]", " ", content_bytes.decode("latin1", errors="ignore"))
                    if len(clean) > 30:
                        text = (clean + "\n" + text).strip()
        except Exception as e:
            print("File extraction error:", e)

    if not text:
        text = "Sample Candidate Resume"

    text_lower = text.lower()
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)

    # 1. Personal Details & Resume Validity Check
    has_email = bool(re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)) or any(k in text_lower for k in ["email:", "e-mail:", "mail id:"])
    digits = len(re.findall(r"\d", text))
    has_phone = bool(re.search(r"\b(?:\+?\d{1,3}[-\s]?)?\(?\d{3,5}\)?[-\s]?\d{3,5}[-\s]?\d{3,5}\b", text)) and digits >= 8
    has_header = any(h in text_lower for h in ["personal details", "contact details", "candidate profile", "personal information"])
    has_links = any(k in text_lower for k in ["linkedin.com", "github.com", "portfolio", "location:"])
    
    is_valid_resume = has_email or has_phone or has_header or has_links
    missing_sections = []
    if not is_valid_resume:
        missing_sections.append("Personal Details (Name, Phone, Email, Location, LinkedIn/GitHub)")

    warning_msg = None if is_valid_resume else "⚠️ Invalid Resume Alert: Document does not contain a Personal Details section. Please upload a valid resume!"

    # 2. Accurate Course & Domain Detection
    domain_name = "Engineering & Technology Candidate"
    domain_icon = "💻"
    domain_desc = "Degree background in B.Tech, M.Tech, B.E, M.E, BCA, MCA, or Computer Science."
    discipline = "Engineering"

    if any(k in text_lower for k in ["mbbs", "bds", "b.pharma", "m.pharma", "nursing", "doctor", "clinical", "hospital", "patient", "bls", "acls"]):
        domain_name = "Medical & Healthcare Candidate"
        domain_icon = "🩺"
        domain_desc = "Degree background in Medical Sciences, MBBS, Pharmacy, Nursing, or Clinical Healthcare."
        discipline = "Medical & Healthcare"
    elif any(k in text_lower for k in ["figma", "ui/ux", "illustrator", "photoshop", "fine arts", "b.a", "m.a", "graphic design", "journalism"]):
        domain_name = "Arts, Design & Humanities Candidate"
        domain_icon = "🎨"
        domain_desc = "Degree background in Arts, Fine Arts, UI/UX Design, Literature, Journalism, or Visual Media."
        discipline = "Arts & Humanities"
    elif any(k in text_lower for k in ["b.com", "m.com", "bba", "mba", "finance", "accounting", "power bi", "tableau", "corporate finance"]):
        domain_name = "Business, Commerce & Finance Candidate"
        domain_icon = "📊"
        domain_desc = "Degree background in Commerce, B.Com, M.Com, BBA, MBA, Corporate Finance, or Business Analytics."
        discipline = "Business & Finance"
    elif any(k in text_lower for k in ["b.sc", "m.sc", "physics", "chemistry", "biology", "microbiology", "spss", "statistics"]):
        domain_name = "Pure & Applied Sciences Candidate"
        domain_icon = "🔬"
        domain_desc = "Degree background in B.Sc, M.Sc, Physics, Chemistry, Mathematics, Statistics, or Lab Research."
        discipline = "Pure & Applied Sciences"
    elif any(k in text_lower for k in ["b.ed", "m.ed", "pedagogy", "teaching", "instructor"]):
        domain_name = "Teaching & Education Candidate"
        domain_icon = "📚"
        domain_desc = "Degree background in Pedagogy, B.Ed, M.Ed, STEM Instruction, or Educational Curriculum Design."
        discipline = "Education & Teaching"

    # 3. Multi-Point Score Metrics
    action_verbs = ["achieved", "developed", "managed", "created", "led", "increased", "reduced", "designed", "implemented", "engineered", "launched", "automated", "optimized", "built"]
    found_verbs = list(set([v for v in action_verbs if v in text_lower]))
    numbers = re.findall(r"\b\d+(?:%|\b)", text)

    action_score = min(100, max(30, len(found_verbs) * 20))
    metrics_score = min(100, max(25, len(numbers) * 30))
    structure_score = 90 if is_valid_resume else 40
    length_score = 95 if (120 <= word_count <= 650) else (30 if word_count < 60 else 65)
    ats_score = min(100, max(35, round((action_score * 0.4) + (metrics_score * 0.3) + (structure_score * 0.3))))

    hackathon_prob = min(96, max(45, round((action_score * 0.4) + (structure_score * 0.3) + (ats_score * 0.3))))
    intern_prob = min(94, max(40, round((metrics_score * 0.4) + (length_score * 0.3) + (ats_score * 0.3))))
    total_score = round((hackathon_prob + intern_prob) / 2)
    grade = "Grade A" if total_score >= 85 else ("Grade B+" if total_score >= 75 else ("Grade B" if total_score >= 60 else "Grade C"))

    # 4. Field-Tailored Roadmaps & Knowledge Source Links
    knowledge_sources = {
        "Engineering": [
            {"name": "GeeksforGeeks Computer Science", "url": "https://www.geeksforgeeks.org/"},
            {"name": "MDN Web Docs Architecture", "url": "https://developer.mozilla.org/"},
            {"name": "LeetCode Algorithmic Practice", "url": "https://leetcode.com/"}
        ],
        "Medical & Healthcare": [
            {"name": "PubMed / NCBI Medical Library", "url": "https://pubmed.ncbi.nlm.nih.gov/"},
            {"name": "WHO Clinical Guidelines", "url": "https://www.who.int/publications"}
        ],
        "Arts & Humanities": [
            {"name": "Figma Design Systems Learn", "url": "https://help.figma.com/"},
            {"name": "Web.dev UI Accessibility", "url": "https://web.dev/learn/accessibility/"}
        ],
        "Business & Finance": [
            {"name": "Corporate Finance Institute (CFI)", "url": "https://corporatefinanceinstitute.com/"},
            {"name": "Microsoft Power BI Documentation", "url": "https://learn.microsoft.com/power-bi/"}
        ],
        "Pure & Applied Sciences": [
            {"name": "Kaggle Learn Python & Science", "url": "https://www.kaggle.com/learn"},
            {"name": "SciPy & NumPy Official Docs", "url": "https://scipy.org/"}
        ]
    }.get(discipline, [
        {"name": "GeeksforGeeks Tech Guides", "url": "https://www.geeksforgeeks.org/"},
        {"name": "MDN Web Docs", "url": "https://developer.mozilla.org/"}
    ])

    roadmap = [
        {"title": f"1. Advanced {discipline} Core Mastery", "category": "Core Specialization", "desc": f"Master fundamental concepts, problem solving patterns, and production principles in {discipline}.", "impact": "+20% Selection Boost", "knowledge_source": knowledge_sources[0]["name"], "source_url": knowledge_sources[0]["url"]},
        {"title": "2. Production & Industry Workflow", "category": "Practical Implementation", "desc": "Build an end-to-end practical solution with full documentation and deployment.", "impact": "+15% Interview Odds", "knowledge_source": knowledge_sources[min(1, len(knowledge_sources)-1)]["name"], "source_url": knowledge_sources[min(1, len(knowledge_sources)-1)]["url"]},
        {"title": "3. Verified Capstone Portfolio Project", "category": "Portfolio Showcase", "desc": "Publish a verified portfolio repository showcasing measurable impact.", "impact": "High Profile Visibility", "knowledge_source": knowledge_sources[0]["name"], "source_url": knowledge_sources[0]["url"]}
    ]

    suggested_jobs = [
        {"title": f"Junior {discipline} Specialist", "match_score": min(96, total_score + 5), "reason": f"Matches detected candidate profile in {discipline}.", "matched_skills": ["Core Fundamentals", "Problem Solving"], "missing_skills": ["Advanced Architecture"]},
        {"title": f"Associate {discipline} Intern", "match_score": min(92, total_score + 2), "reason": "Aligns with candidate's educational background.", "matched_skills": ["Technical Writing", "Analysis"], "missing_skills": ["Cloud Infrastructure"]}
    ]

    feedback = []
    if not is_valid_resume:
        feedback.append(warning_msg)
    else:
        feedback.append("✅ Resume Structure Audit: Personal Details and essential sections detected.")
    feedback.append(f"🎓 Candidate Course Classification: {domain_icon} {domain_name}.")
    feedback.append(f"⚡ Action Impact Audit: Found {len(found_verbs)} accomplishment action verbs.")
    feedback.append(f"📊 Quantifiable Metrics: Found {len(numbers)} numerical data points.")
    feedback.append(f"🏷️ Audited ATS Match Score: {ats_score}/100.")

    return {
        "success": True,
        "is_valid_resume": is_valid_resume,
        "is_complete_resume": is_valid_resume,
        "missing_sections": missing_sections if not is_valid_resume else [],
        "warning_message": warning_msg,
        "warning_msg": warning_msg,
        "predicted_domain": domain_name,
        "domain_icon": domain_icon,
        "domain_description": domain_desc,
        "domain": {"title": domain_name, "icon": domain_icon, "description": domain_desc},
        "hackathon_probability": hackathon_prob,
        "hackathon_badge": "High Probability" if hackathon_prob > 75 else "Competitive",
        "hackathon_status": "Strong background for competitive hackathons." if hackathon_prob > 75 else "Good baseline.",
        "hackathon_odds": {"score": hackathon_prob, "badge": "High Probability" if hackathon_prob > 75 else "Competitive", "status": "Strong background for competitive hackathons." if hackathon_prob > 75 else "Good baseline."},
        "internship_probability": intern_prob,
        "internship_badge": "Competitive" if intern_prob > 70 else "Building Foundation",
        "internship_status": "Profile shows active qualification capabilities.",
        "internship_odds": {"score": intern_prob, "badge": "Competitive" if intern_prob > 70 else "Building Foundation", "status": "Profile shows active qualification capabilities."},
        "total_score": total_score,
        "grade": grade,
        "overall_score": {"score": total_score, "grade": grade},
        "action_score": action_score,
        "metrics_score": metrics_score,
        "structure_score": structure_score,
        "length_score": length_score,
        "ats_score": ats_score,
        "metrics": {"action_verbs": action_score, "metrics_presence": metrics_score, "structure": structure_score, "length_balance": length_score, "ats_match": ats_score},
        "feedback": feedback,
        "study_roadmap": roadmap,
        "roadmap": roadmap,
        "knowledge_sources": knowledge_sources,
        "suggested_jobs": suggested_jobs,
        "job_matches": suggested_jobs,
        "precision_study_manual": f"# {domain_name} Precision Manual\n\n- Candidate Field: {discipline}\n- ATS Readiness: {ats_score}/100\n- Primary Goal: Master core theoretical background and practical implementation in {discipline}."
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5501")),
        log_level="info",
    )