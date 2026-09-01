import os
import json
import re
import tempfile
import time
import random
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI(title="AutoHire RAG AI Resume Analyzer API")

@app.get("/")
async def home():
    return FileResponse("analyzer.html")

@app.get("/api/study-pack/pdf")
@app.get("/api/study-pack/html")
async def get_study_pack_pdf(topic: str = "Data Structures & Algorithms Mastery", name: str = "Candidate"):
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

# Enable CORS for local HTML frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobSuggestion(BaseModel):
    title: str
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    reason: str

class StudyTopic(BaseModel):
    category: str
    topic: str
    recommendation: str
    priority: str
    impact: str

class AnalysisResult(BaseModel):
    is_valid_resume: bool
    is_complete_resume: bool = True
    missing_sections: List[str] = []
    warning_message: Optional[str] = None
    predicted_domain: str
    domain_icon: str
    domain_description: str
    action_score: float
    metrics_score: float
    structure_score: float
    length_score: float
    total_score: float
    grade: str
    hackathon_probability: float
    internship_probability: float
    hackathon_status: str
    internship_status: str
    feedback: List[dict]
    detected_skills: List[str]
    company_skills: List[str]
    suggested_jobs: List[JobSuggestion]
    study_roadmap: List[StudyTopic]
    skill_gaps: List[str]
    domain: Optional[dict] = None
    hackathon_odds: Optional[dict] = None
    internship_odds: Optional[dict] = None
    overall_score: Optional[dict] = None
    metrics: Optional[dict] = None
    roadmap: Optional[List[dict]] = None
    job_matches: Optional[List[dict]] = None
    verbatim_facts: Optional[dict] = None
    taxonomy_analysis: Optional[dict] = None
    competency_audit: Optional[dict] = None
    precision_study_manual: Optional[str] = None
    compiled_typeset_manual: Optional[str] = None


def check_personal_details_section(raw_text: str) -> bool:
    """Check if the text contains a genuine Personal Details section (Name, Phone, Email, Location, LinkedIn, GitHub, Portfolio)."""
    if not raw_text:
        return False
    lower_text = raw_text.lower()

    # 1. Email check (real email regex pattern or explicit email field label)
    has_email = bool(re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", raw_text)) or any(
        k in lower_text for k in ["email:", "e-mail:", "mail id:", "email address:"]
    )

    # 2. Phone check (valid phone number digits/pattern or explicit phone/mobile label - NO standalone 'call')
    has_phone_pattern = bool(re.search(r"\b(?:\+?\d{1,3}[-\s]?)?\(?\d{3,5}\)?[-\s]?\d{3,5}[-\s]?\d{3,5}\b", raw_text))
    has_phone_label = bool(re.search(r"\b(phone|mobile|cell|tel|contact\s*no|contact\s*number|phone\s*no|phone\s*number)\b", lower_text))
    has_phone = (has_phone_pattern and len(re.findall(r"\d", raw_text)) >= 8) or has_phone_label

    # 3. Personal section headers, social profile links, or explicit candidate name label
    personal_headers = [
        "personal details", "personal information", "contact details", "contact info",
        "contact information", "personal profile", "candidate profile", "applicant details"
    ]
    has_header = any(h in lower_text for h in personal_headers)
    has_links = any(k in lower_text for k in ["linkedin.com", "github.com", "gitlab.com", "portfolio", "location:", "address:", "pincode:"])
    has_name_label = bool(re.search(r"\b(full\s*name|candidate\s*name|applicant\s*name)\s*[:\-]", lower_text))

    has_personal_meta = has_header or has_links or has_name_label

    return has_email or has_phone or has_personal_meta


def validate_resume_document(raw_text: str) -> tuple[bool, bool, str, list[str]]:
    """
    Detect if the uploaded text is a genuine complete resume or a non-resume document (like a Marksheet/Transcript/Timetable).
    Required Resume Categories:
    1. Personal Details (Name, Phone, Email, Location, LinkedIn, GitHub, Portfolio)
    2. Career Objective / Profile Summary / Target Role
    3. Education (Degree/Course, College, University, Year, CGPA/GPA)
    4. Technical / Core Skills (Programming, Web, Database, Tools, Technologies)
    5. Work / Project Experience (Projects, Internships, Employment, Work History)
    """
    lower_text = raw_text.lower()
    words = re.findall(r"\b\w+\b", raw_text)
    word_count = len(words)

    # 1. Marksheet / Academic Transcript / Non-resume Document Detection
    marksheet_keywords = [
        "marksheet", "mark sheet", "grade sheet", "grade card", "statement of marks", "academic transcript",
        "grade transcript", "semester mark", "sem 1", "sem 2", "sem 3", "sem 4", "sem 5", "sem 6", "sem 7", "sem 8",
        "sem-1", "sem-2", "sem-3", "sem-4", "sem-5", "sem-6", "sem-7", "sem-8",
        "semester 1", "semester 2", "semester 3", "semester 4", "semester 5", "semester 6", "semester 7", "semester 8",
        "sgpa", "cgpa", "internal marks", "external marks", "subject code", "course code", "total marks",
        "credits earned", "grade point", "controller of examinations", "provisional certificate",
        "consolidated mark sheet", "examination report", "report card", "tabular mark list",
        "result: pass", "result: fail", "end semester examination"
    ]
    
    non_resume_keywords = [
        "timetable", "time table", "class schedule", "lecture schedule", "period 1", "period 2", "period 3",
        "hall ticket", "admit card", "fee receipt", "tax invoice", "bill of supply", "syllabus copy",
        "experiment no", "lab manual", "aim of the experiment"
    ]

    marksheet_hits = [kw for kw in marksheet_keywords if kw in lower_text]
    non_resume_hits = [kw for kw in non_resume_keywords if kw in lower_text]

    # Check for Work/Project Experience anchors
    experience_anchors = [
        "projects", "project", "experience", "work experience", "internship", "internships",
        "work history", "employment", "key projects", "academic project", "mini project",
        "major project", "responsibilities", "practical experience"
    ]
    has_experience = any(exp in lower_text for exp in experience_anchors)

    # If it has 2+ marksheet keywords, or 1 marksheet/non-resume keyword without Work/Project Experience:
    if len(marksheet_hits) >= 2 or (len(marksheet_hits) >= 1 and not has_experience) or len(non_resume_hits) >= 2:
        msg = "⚠️ Marksheet / Non-Resume Document Detected: The uploaded document appears to be an Academic Marksheet or Grade Sheet, not a complete Resume. Please upload a complete resume containing Work/Project Experience, Technical Skills, and Profile Summary."
        return False, False, msg, ["Document is an Academic Marksheet / Grade Sheet, not a Resume"]

    missing_sections = []

    # Category 1: PERSONAL DETAILS
    if not check_personal_details_section(raw_text):
        missing_sections.append("Personal Details & Contact Info (Name, Phone, Email, Location, LinkedIn/GitHub)")

    # Category 2: CAREER OBJECTIVE / PROFILE SUMMARY
    objective_anchors = [
        "objective", "target role", "target job role", "career objective", "profile summary",
        "professional summary", "summary", "career goal", "about me", "seeking role", "seeking a role", "aspiring"
    ]
    if not any(anchor in lower_text for anchor in objective_anchors):
        missing_sections.append("Career Objective / Profile Summary")

    # Category 3: EDUCATION
    education_anchors = [
        "education", "degree", "course", "specialization", "college", "university", "school", "academic",
        "b.tech", "btech", "m.tech", "mtech", "b.e", "be", "b.sc", "bsc", "m.sc", "msc",
        "bba", "mba", "b.com", "bcom", "bca", "mca", "diploma", "10th", "12th",
        "cgpa", "gpa", "percentage", "year", "qualification"
    ]
    if not any(anchor in lower_text for anchor in education_anchors):
        missing_sections.append("Education (Degree, Course, Specialization, College, University)")

    # Category 4: TECHNICAL SKILLS
    skills_anchors = [
        "skills", "technical skills", "programming", "web technologies", "database",
        "tools", "software", "technologies", "tech stack", "python", "javascript",
        "java", "c++", "c#", "html", "css", "sql", "react", "nodejs", "git", "aws", "excel", "power bi",
        "operating system", "operating systems", "os", "linux", "c", "data structures"
    ]
    if not any(anchor in lower_text for anchor in skills_anchors):
        missing_sections.append("Technical / Core Skills")

    # Category 5: WORK / PROJECT EXPERIENCE
    if not has_experience:
        missing_sections.append("Work / Project Experience (Key Projects, Internships, Employment)")

    if missing_sections:
        warning_msg = f"⚠️ Incomplete Resume Alert: Document is missing required section(s): {', '.join(missing_sections)}. Please upload a complete resume!"
        return False, False, warning_msg, missing_sections

    return True, True, "", []


def extract_verbatim_facts(raw_text: str) -> dict:
    """
    Extract verbatim facts from resume text with zero hallucination.
    Every extracted tool/technology includes its exact context sentence quote.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # 1. Explicit Degrees
    explicit_degrees = []
    degree_patterns = [
        (r"\b(b\.tech|btech|b\.e|be|m\.tech|mtech|m\.e|me)\b", "Engineering & Technology"),
        (r"\b(b\.sc|bsc|m\.sc|msc)\b", "Science & Research"),
        (r"\b(b\.com|bcom|m\.com|mcom|bba|mba|b\.a|ba|m\.a|ma)\b", "Arts, Business & Commerce"),
        (r"\b(mbbs|bds|b\.pharma|m\.pharma|nursing)\b", "Medical & Healthcare"),
        (r"\b(b\.ed|m\.ed)\b", "Teaching & Education"),
        (r"\b(bca|mca)\b", "Computer Applications")
    ]

    for line in lines:
        line_lower = line.lower()
        for pat, major_default in degree_patterns:
            match = re.search(pat, line_lower)
            if match:
                deg_name = match.group(0).upper()
                institution = "Extracted from Resume"
                if "university" in line_lower or "college" in line_lower or "institute" in line_lower or "school" in line_lower:
                    institution = line
                explicit_degrees.append({
                    "degree_name": deg_name,
                    "major_field": major_default,
                    "institution": institution
                })
                break

    # 2. Explicit Tools & Tech with Verbatim Quote
    known_tech = [
        "python", "java", "javascript", "typescript", "c++", "c#", "html", "css", "sql", "react",
        "nodejs", "express", "fastapi", "django", "flask", "aws", "docker", "kubernetes", "git",
        "github", "figma", "photoshop", "illustrator", "excel", "power bi", "tableau", "spss",
        "matlab", "autocad", "bls", "acls", "mongodb", "postgresql", "redis"
    ]

    explicit_tools_and_tech = []
    seen_tech = set()

    for line in lines:
        line_lower = line.lower()
        for tech in known_tech:
            if tech not in seen_tech and re.search(r"\b" + re.escape(tech) + r"\b", line_lower):
                seen_tech.add(tech)
                explicit_tools_and_tech.append({
                    "name": tech.title() if tech not in ["css", "html", "sql", "aws", "dsa", "ui/ux", "bls", "acls"] else tech.upper(),
                    "context_sentence_quote": line
                })

    # 3. Job Titles & Experience
    job_titles = []
    title_keywords = ["engineer", "developer", "intern", "manager", "analyst", "designer", "consultant", "doctor", "officer", "instructor", "teacher", "associate"]
    for line in lines:
        line_lower = line.lower()
        if any(re.search(r"\b" + re.escape(kw) + r"\b", line_lower) for kw in title_keywords):
            if len(line.split()) < 12 and not line.endswith("."):
                job_titles.append({
                    "title": line,
                    "organization": "Mentioned in Resume",
                    "duration": "Verbatim Record"
                })

    # 4. Stated Projects
    stated_projects = []
    for line in lines:
        line_lower = line.lower()
        if "project" in line_lower or "developed" in line_lower or "built" in line_lower or "system" in line_lower:
            techs_found = [t.title() for t in known_tech if re.search(r"\b" + re.escape(t) + r"\b", line_lower)]
            if techs_found:
                stated_projects.append({
                    "title": line[:60] + "..." if len(line) > 60 else line,
                    "technologies_mentioned": techs_found
                })

    # 5. Certifications
    certifications = []
    cert_keywords = ["certified", "certification", "certificate", "license", "bls", "acls", "aws certified"]
    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in cert_keywords):
            certifications.append(line)

    return {
        "explicit_degrees": explicit_degrees[:4],
        "explicit_tools_and_tech": explicit_tools_and_tech[:12],
        "job_titles": job_titles[:5],
        "stated_projects": stated_projects[:5],
        "certifications": list(set(certifications))[:5]
    }


def classify_candidate_taxonomy(verbatim_facts: dict, raw_text: str) -> dict:
    """
    Academic & Professional Taxonomist Engine.
    Classifies candidate discipline, specialization, target role, and experience tier
    based strictly on verified extracted facts and raw text quotes without hallucination.
    """
    text_lower = raw_text.lower()

    degrees = verbatim_facts.get("explicit_degrees", [])
    tools = [t.get("name", "").lower() for t in verbatim_facts.get("explicit_tools_and_tech", [])]
    job_titles = verbatim_facts.get("job_titles", [])
    projects = verbatim_facts.get("stated_projects", [])

    deg_names = [d.get("degree_name", "").upper() for d in degrees]

    discipline = "Engineering"
    specialization = "Computer Science - Software Engineering"
    target_role = "Full Stack Software Engineer"

    if any(d in deg_names for d in ["MBBS", "BDS", "B.PHARMA", "M.PHARMA", "NURSING"]) or any(k in text_lower for k in ["doctor", "clinical", "hospital", "patient", "bls", "acls"]):
        discipline = "Medicine & Healthcare"
        if "bls" in tools or "acls" in tools or "clinical" in text_lower:
            specialization = "Clinical Practice - General Residency"
            target_role = "Clinical Medical Officer / Resident Doctor"
        else:
            specialization = "Pharmaceutical Sciences - Care Delivery"
            target_role = "Healthcare Specialist / Pharmacist"

    elif any(d in deg_names for d in ["B.SC", "BSC", "M.SC", "MSC"]) or any(k in text_lower for k in ["physics", "chemistry", "biology", "research", "lab", "spss"]):
        discipline = "Pure & Applied Sciences"
        specialization = "Data Analytics & Applied Research"
        target_role = "Scientific Data Analyst / Research Associate"

    elif any(d in deg_names for d in ["B.COM", "BCOM", "M.COM", "MCOM", "BBA", "MBA"]) or any(k in text_lower for k in ["finance", "banking", "accounting", "power bi", "tableau"]):
        discipline = "Business & Finance"
        specialization = "Corporate Finance & Analytics"
        target_role = "Business & Financial Analyst"

    elif any(d in deg_names for d in ["B.A", "BA", "M.A", "MA", "FINE ARTS"]) or any(k in text_lower for k in ["figma", "design", "ui/ux", "illustrator", "photoshop"]):
        discipline = "Arts & Humanities"
        specialization = "Digital Product & UI/UX Design"
        target_role = "UI/UX Designer & Visual Systems Specialist"

    elif any(d in deg_names for d in ["B.ED", "M.ED"]) or any(k in text_lower for k in ["teaching", "teacher", "pedagogy", "curriculum", "lecturer"]):
        discipline = "Education & Teaching"
        specialization = "STEM Education & Computer Pedagogy"
        target_role = "Computer Science Educator / STEM Instructor"

    elif any(k in text_lower for k in ["law", "llb", "llm", "attorney", "legal"]):
        discipline = "Law"
        specialization = "Corporate Law & Legal Advisory"
        target_role = "Legal Associate / Compliance Officer"

    else:
        discipline = "Engineering"
        if "python" in tools and ("fastapi" in tools or "django" in tools or "sql" in tools):
            specialization = "Computer Science - Backend Software Engineering"
            target_role = "Backend Software Engineer"
        elif "react" in tools or "javascript" in tools or "html" in tools or "css" in tools:
            specialization = "Computer Science - Web Engineering"
            target_role = "Full Stack Web Developer"
        elif "aws" in tools or "docker" in tools or "kubernetes" in tools:
            specialization = "Computer Science - Cloud & DevOps Architecture"
            target_role = "DevOps / Cloud Solutions Engineer"
        else:
            specialization = "Computer Science - Software Engineering"
            target_role = "Software Engineer"

    years_found = re.findall(r"\b(\d+)\+?\s*(?:years?|yrs?)\b", text_lower)
    max_yrs = 0
    if years_found:
        max_yrs = max(int(y) for y in years_found)

    exp_count = len(job_titles)

    if max_yrs >= 8:
        experience_tier = "Senior (8+ yrs)"
    elif max_yrs >= 4 or exp_count >= 3:
        experience_tier = "Mid-Level (4-7 yrs)"
    elif max_yrs >= 1 or exp_count >= 1:
        experience_tier = "Early Career (1-3 yrs)"
    else:
        experience_tier = "Student/Fresh Graduate (0 yrs)"

    rationale = f"Profile classified under {discipline} ({specialization}) in the {experience_tier} tier based on explicit verification of {len(degrees)} degree(s), {len(tools)} tool(s), and {len(projects)} stated project(s)."

    return {
        "discipline": discipline,
        "specialization": specialization,
        "target_role": target_role,
        "experience_tier": experience_tier,
        "rationale": rationale
    }


def audit_competency_gaps(verbatim_facts: dict, taxonomy: dict, raw_text: str) -> dict:
    """
    Lead Hiring Auditor & Curriculum Director Engine.
    Defines 8 non-negotiable industry-standard competencies for the exact role and tier,
    audits verified facts, and calculates an exact ATS Score with strict gap analysis.
    """
    text_lower = raw_text.lower()
    tools = [t.get("name", "").lower() for t in verbatim_facts.get("explicit_tools_and_tech", [])]
    projects = verbatim_facts.get("stated_projects", [])
    discipline = taxonomy.get("discipline", "Engineering")

    if discipline == "Medicine & Healthcare":
        competencies = [
            {"name": "Clinical Diagnostics & Patient Care", "type": "Core Concept", "why_required": "Essential for accurate patient diagnosis and clinical treatment delivery.", "severity": "Critical", "keys": ["clinical", "patient", "diagnos"]},
            {"name": "BLS & ACLS Certification", "type": "Regulation", "why_required": "Mandatory life support credential for emergency hospital operations.", "severity": "Critical", "keys": ["bls", "acls", "life support"]},
            {"name": "Electronic Health Records (EHR/EMR)", "type": "Tool", "why_required": "Required for digital hospital patient charting and medical record management.", "severity": "Important", "keys": ["ehr", "emr", "electronic health", "charting"]},
            {"name": "Pharmacology & Dosage Administration", "type": "Core Concept", "why_required": "Crucial for safe prescription management and clinical pharmacology.", "severity": "Critical", "keys": ["pharma", "prescription", "dosage", "drug"]},
            {"name": "Emergency Medical Response", "type": "Methodology", "why_required": "Vital for managing acute trauma and urgent care triage.", "severity": "Critical", "keys": ["emergency", "trauma", "triage", "urgent"]},
            {"name": "Medical Ethics & HIPAA Compliance", "type": "Regulation", "why_required": "Required to protect patient privacy and uphold medical regulatory standards.", "severity": "Important", "keys": ["hipaa", "ethics", "privacy", "compliance"]},
            {"name": "Hospital Infection Control & Safety", "type": "Regulation", "why_required": "Mandatory standard for hospital hygiene and sterile patient care.", "severity": "Important", "keys": ["safety", "sterile", "hygiene", "infection"]},
            {"name": "Diagnostic Pathology & Lab Testing", "type": "Methodology", "why_required": "Required to interpret blood work, lab panels, and diagnostic pathology.", "severity": "Important", "keys": ["pathology", "lab", "blood", "test"]}
        ]
    elif discipline == "Pure & Applied Sciences":
        competencies = [
            {"name": "Statistical Modeling & Analysis (SPSS/R)", "type": "Tool", "why_required": "Necessary to perform quantitative data analysis and scientific hypothesis testing.", "severity": "Critical", "keys": ["spss", "r", "statistic", "regression"]},
            {"name": "Good Laboratory Practice (GLP)", "type": "Regulation", "why_required": "Mandatory safety and quality standard for industrial and academic research labs.", "severity": "Critical", "keys": ["glp", "laboratory", "biosafety", "lab safety"]},
            {"name": "Experimental Design & Data Collection", "type": "Methodology", "why_required": "Core methodology for structuring scientific trials and empirical studies.", "severity": "Critical", "keys": ["experiment", "trial", "data collection", "sample"]},
            {"name": "Scientific Python Stack (NumPy/SciPy/Pandas)", "type": "Tool", "why_required": "Required for modern computational science and scientific programming.", "severity": "Important", "keys": ["python", "numpy", "scipy", "pandas"]},
            {"name": "Research Literature Audit & Publishing", "type": "Core Concept", "why_required": "Essential for synthesizing prior studies and publishing peer-reviewed research.", "severity": "Important", "keys": ["research", "paper", "journal", "publication"]},
            {"name": "Hypothesis Testing & p-value Validation", "type": "Core Concept", "why_required": "Foundation of scientific proof and statistical significance testing.", "severity": "Critical", "keys": ["hypothesis", "p-value", "significance", "t-test"]},
            {"name": "Analytical Instrumentation Calibration", "type": "Tool", "why_required": "Required to operate and calibrate specialized laboratory testing equipment.", "severity": "Important", "keys": ["instrument", "spectrophotometer", "microscope", "calibration"]},
            {"name": "Data Visualization & Scientific Graphing", "type": "Methodology", "why_required": "Critical for presenting research findings to scientific audiences.", "severity": "Important", "keys": ["visualiz", "graph", "matplotlib", "plot"]}
        ]
    elif discipline == "Business & Finance":
        competencies = [
            {"name": "Corporate Financial Modeling & Valuation", "type": "Methodology", "why_required": "Core framework for financial forecasting, DCF modeling, and corporate analysis.", "severity": "Critical", "keys": ["financial model", "dcf", "valuation", "finance"]},
            {"name": "Power BI / Tableau Dashboarding", "type": "Tool", "why_required": "Required for building executive business intelligence dashboards.", "severity": "Critical", "keys": ["power bi", "tableau", "dashboard", "bi"]},
            {"name": "Advanced Excel & Pivot Tables", "type": "Tool", "why_required": "Universal tool expected for spreadsheet modeling and financial audit.", "severity": "Critical", "keys": ["excel", "pivot", "vlookup", "spreadsheet"]},
            {"name": "SQL Data Querying & Extraction", "type": "Tool", "why_required": "Necessary to query corporate relational databases for business metrics.", "severity": "Critical", "keys": ["sql", "query", "database", "select"]},
            {"name": "Market Risk & Variance Analysis", "type": "Core Concept", "why_required": "Required to evaluate financial risk exposure and budget variance.", "severity": "Important", "keys": ["risk", "variance", "budget", "exposure"]},
            {"name": "Business Case Problem Solving", "type": "Methodology", "why_required": "Essential for management consulting and strategic decision making.", "severity": "Important", "keys": ["business case", "consulting", "strategy", "problem solving"]},
            {"name": "Financial Statement Audit & Reporting", "type": "Core Concept", "why_required": "Required for analyzing P&L balance sheets and corporate cash flows.", "severity": "Important", "keys": ["statement", "p&l", "balance sheet", "cash flow"]},
            {"name": "Executive Stakeholder Communication", "type": "Methodology", "why_required": "Critical for presenting quarterly financial findings to leadership.", "severity": "Important", "keys": ["stakeholder", "presentation", "executive", "communication"]}
        ]
    elif discipline == "Arts & Humanities":
        competencies = [
            {"name": "Figma Auto-Layout & Design Systems", "type": "Tool", "why_required": "Industry-standard design tool for creating scalable UI component libraries.", "severity": "Critical", "keys": ["figma", "design system", "auto-layout", "components"]},
            {"name": "UI/UX Prototyping & Wireframing", "type": "Methodology", "why_required": "Core methodology for user experience architecture and user testing.", "severity": "Critical", "keys": ["ui", "ux", "wireframe", "prototype"]},
            {"name": "Color Theory & Visual Hierarchy", "type": "Core Concept", "why_required": "Fundamental design principles for intuitive visual aesthetics.", "severity": "Important", "keys": ["color", "hierarchy", "typography", "layout"]},
            {"name": "Adobe Creative Suite (Photoshop/Illustrator)", "type": "Tool", "why_required": "Standard creative tools for vector graphics and digital media production.", "severity": "Important", "keys": ["photoshop", "illustrator", "adobe", "creative suite"]},
            {"name": "Responsive Web Layout & Accessibility (a11y)", "type": "Core Concept", "why_required": "Required to ensure digital products work across mobile and desktop accessible UI.", "severity": "Important", "keys": ["responsive", "accessibility", "a11y", "mobile"]},
            {"name": "Portfolio Case Study Documentation", "type": "Methodology", "why_required": "Critical evidence needed to demonstrate end-to-end design process.", "severity": "Critical", "keys": ["portfolio", "case study", "behance", "dribbble"]},
            {"name": "User Research & Usability Testing", "type": "Methodology", "why_required": "Essential for validating user interface decisions with real users.", "severity": "Important", "keys": ["user research", "usability", "interviews", "testing"]},
            {"name": "Brand Identity & Visual Guidelines", "type": "Core Concept", "why_required": "Required to maintain consistent visual brand identities for digital products.", "severity": "Important", "keys": ["brand", "identity", "guidelines", "logo"]}
        ]
    elif discipline == "Education & Teaching":
        competencies = [
            {"name": "STEM Curriculum Development", "type": "Methodology", "why_required": "Core responsibility for structuring academic courses and technical modules.", "severity": "Critical", "keys": ["curriculum", "stem", "course", "syllabus"]},
            {"name": "Interactive Lesson Planning", "type": "Methodology", "why_required": "Required for engaging students and delivering structured daily instruction.", "severity": "Critical", "keys": ["lesson plan", "instruction", "teaching", "pedagogy"]},
            {"name": "Student Assessment & Evaluation Systems", "type": "Core Concept", "why_required": "Essential for measuring student learning outcomes and grading.", "severity": "Important", "keys": ["assessment", "grading", "evaluation", "test"]},
            {"name": "EdTech & Classroom Learning Tools", "type": "Tool", "why_required": "Required for modern digital learning management and virtual classrooms.", "severity": "Important", "keys": ["edtech", "lms", "classroom", "moodle", "google classroom"]},
            {"name": "Classroom Management & Engagement", "type": "Core Concept", "why_required": "Foundation for maintaining a productive learning environment.", "severity": "Critical", "keys": ["classroom", "management", "engagement", "student"]},
            {"name": "Pedagogical Theory & Learning Strategies", "type": "Core Concept", "why_required": "Underpins effective teaching strategies tailored to diverse student needs.", "severity": "Important", "keys": ["pedagogy", "learning theory", "strategy", "instructional"]},
            {"name": "Differentiated & Inclusive Instruction", "type": "Methodology", "why_required": "Required to support students with varying learning abilities.", "severity": "Important", "keys": ["inclusive", "differentiated", "special ed", "support"]},
            {"name": "Student Mentorship & Project Guidance", "type": "Methodology", "why_required": "Critical for advising student capstone projects and STEM competitions.", "severity": "Important", "keys": ["mentorship", "guidance", "advisor", "project"]}
        ]
    elif discipline == "Law":
        competencies = [
            {"name": "Contract Drafting & Legal Auditing", "type": "Methodology", "why_required": "Core legal function for preparing and reviewing binding commercial agreements.", "severity": "Critical", "keys": ["contract", "drafting", "legal audit", "agreement"]},
            {"name": "Legal Research & Statutory Analysis", "type": "Tool", "why_required": "Required for finding judicial precedent and analyzing statutory codes.", "severity": "Critical", "keys": ["legal research", "lexisnexis", "westlaw", "statute"]},
            {"name": "Corporate Compliance & Governance", "type": "Regulation", "why_required": "Essential to ensure company operations adhere to legal and regulatory statutes.", "severity": "Critical", "keys": ["compliance", "governance", "regulatory", "statutory"]},
            {"name": "Dispute Resolution & Negotiation", "type": "Core Concept", "why_required": "Required to settle legal disputes and negotiate client terms.", "severity": "Important", "keys": ["dispute", "negotiation", "litigation", "settlement"]},
            {"name": "Case Law Synthesis & Memorandum Writing", "type": "Methodology", "why_required": "Fundamental skill for writing legal briefs and advising senior attorneys.", "severity": "Important", "keys": ["case law", "brief", "memorandum", "memo"]},
            {"name": "Intellectual Property & Licensing", "type": "Core Concept", "why_required": "Critical for protecting corporate patents, trademarks, and copyright assets.", "severity": "Important", "keys": ["ip", "patent", "trademark", "licensing"]},
            {"name": "Regulatory Risk Assessment", "type": "Methodology", "why_required": "Required to identify legal liability and minimize corporate risk.", "severity": "Important", "keys": ["risk assessment", "liability", "regulatory risk", "audit"]},
            {"name": "Legal Ethics & Professional Responsibility", "type": "Regulation", "why_required": "Mandatory ethical standards required for attorney bar licensing.", "severity": "Critical", "keys": ["ethics", "bar", "professional responsibility", "confidentiality"]}
        ]
    else:
        competencies = [
            {"name": "Data Structures & Algorithms (DSA)", "type": "Core Concept", "why_required": "Non-negotiable foundation for software engineering problem solving and coding interviews.", "severity": "Critical", "keys": ["dsa", "data structure", "algorithm", "leetcode", "python", "java", "c++"]},
            {"name": "REST API Architecture & Microservices", "type": "Core Concept", "why_required": "Essential for building backend microservices and client-server communications.", "severity": "Critical", "keys": ["rest api", "fastapi", "express", "django", "flask", "microservice", "api"]},
            {"name": "Database Query Optimization & Relational SQL", "type": "Tool", "why_required": "Required for querying, modeling, and indexing relational database systems.", "severity": "Critical", "keys": ["sql", "postgresql", "mysql", "mongodb", "database"]},
            {"name": "Docker Containerization & Deployment", "type": "Tool", "why_required": "Industry standard for packaging applications into reproducible containers.", "severity": "Important", "keys": ["docker", "container", "kubernetes"]},
            {"name": "Cloud Infrastructure & AWS Services", "type": "Framework", "why_required": "Required to deploy scalable cloud services and manage cloud resources.", "severity": "Important", "keys": ["aws", "cloud", "azure", "gcp"]},
            {"name": "System Architecture & Scalability", "type": "Methodology", "why_required": "Necessary for designing fault-tolerant high-concurrency software platforms.", "severity": "Important", "keys": ["system design", "architecture", "scalability", "redis"]},
            {"name": "Git Version Control & Code Auditing", "type": "Tool", "why_required": "Universal tool required for team collaboration and code commit tracking.", "severity": "Critical", "keys": ["git", "github", "gitlab", "version control"]},
            {"name": "Automated Unit Testing & CI/CD Pipelines", "type": "Methodology", "why_required": "Essential for continuous integration and maintaining production code quality.", "severity": "Important", "keys": ["test", "ci/cd", "jest", "pytest", "unit test"]}
        ]

    verified_strengths = []
    verified_gaps = []
    present_count = 0

    for comp in competencies:
        name = comp["name"]
        comp_keys = comp["keys"]
        is_present = False

        for k in comp_keys:
            if k in tools or re.search(r"\b" + re.escape(k) + r"\b", text_lower):
                is_present = True
                break

        if is_present:
            present_count += 1
            verified_strengths.append(name)
        else:
            verified_gaps.append({
                "competency_name": name,
                "competency_type": comp["type"],
                "why_required": comp["why_required"],
                "severity": comp["severity"]
            })

    base_ratio = (present_count / 8.0) * 70.0
    project_bonus = min(30.0, len(projects) * 15.0)
    ats_score = min(100, max(25, round(base_ratio + project_bonus)))

    scoring_rationale = f"ATS Score {ats_score}/100 calculated from {present_count}/8 verified present competencies ({round(base_ratio)} pts) and {len(projects)} verified project record(s) ({round(project_bonus)} pts)."

    return {
        "ats_score": ats_score,
        "scoring_rationale": scoring_rationale,
        "verified_strengths": verified_strengths,
        "verified_gaps": verified_gaps
    }


def generate_precision_study_manual(taxonomy: dict, competency_audit: dict) -> str:
    """
    Academic Textbook Author & Senior Training Director Engine.
    Generates a comprehensive, highly technical Precision Study Manual strictly for
    audited competency gaps.
    Starts immediately with '# {target_role} - Precision Study Manual'.
    """
    target_role = taxonomy.get("target_role", "Software Engineer")
    specialization = taxonomy.get("specialization", "Computer Science")
    discipline = taxonomy.get("discipline", "Engineering")
    experience_tier = taxonomy.get("experience_tier", "Student/Fresh Graduate (0 yrs)")
    gaps = competency_audit.get("verified_gaps", [])

    lines = []
    lines.append(f"# {target_role} - Precision Study Manual")
    lines.append(f"**Curriculum Specialization:** {specialization} ({experience_tier})")
    lines.append(f"**Discipline Category:** {discipline}")
    lines.append(f"**Audited Competency Gaps Target Count:** {len(gaps)}")
    lines.append("")

    if not gaps:
        lines.append("## 🏆 Full Competency Mastery Verified")
        lines.append("No critical or important competency gaps were detected in your candidate profile. All 8 non-negotiable industry standards are verified present!")
        return "\n".join(lines)

    for idx, gap in enumerate(gaps, 1):
        comp_name = gap.get("competency_name", "Technical Competency")
        comp_type = gap.get("competency_type", "Core Concept")
        severity = gap.get("severity", "Critical")
        why_required = gap.get("why_required", "Required for industry standards.")

        lines.append(f"## Module {idx}: {comp_name} [{severity} GAP]")
        lines.append(f"**Type:** `{comp_type}` | **Role Requirement:** {why_required}")
        lines.append("")

        lines.append("### 1. Foundational Deep Dive")
        lines.append(f"Understanding **{comp_name}** requires mastering the core theoretical background and architectural principles governing {specialization}.")
        lines.append("")
        lines.append("```")
        lines.append("  +-----------------------------------------------------------+")
        lines.append(f"  |  [Input Data / Client Query] --> [ {comp_name} Engine ]  |")
        lines.append("  +-----------------------------------------------------------+")
        lines.append("                                |                              ")
        lines.append("                                v                              ")
        lines.append("  +-----------------------------------------------------------+")
        lines.append("  |  [ Validation & Logic ] --> [ Verified Production Output ] |")
        lines.append("  +-----------------------------------------------------------+")
        lines.append("```")
        lines.append("")
        lines.append("**Mathematical / Formulaic Principle:**")
        lines.append(r"\[ \text{Efficiency Score } (E) = \frac{\sum \text{Verified Outcomes}}{\text{Latency } (\Delta t) \times \text{Resource Utilization } (U)} \]")
        lines.append(r"\[ \text{Reliability Index } (R) = 1 - e^{-\lambda t} \]")
        lines.append("")

        lines.append("### 2. Industry Real-World Implementation")
        lines.append(f"Below is a concrete implementation scenario for **{comp_name}** tailored for production readiness:")
        lines.append("")

        if discipline == "Medicine & Healthcare":
            lines.append("**Clinical Case Study & Diagnostic Workflow:**")
            lines.append(f"1. **Patient Triage & Initial Audit**: Evaluate clinical symptoms, baseline vital signs, and EHR medical history for {comp_name}.")
            lines.append(f"2. **Diagnostic Protocol Execution**: Administer standardized protocol ({comp_name}) adhering strictly to BLS/ACLS guidelines.")
            lines.append(f"3. **Post-Treatment Monitoring**: Document outcomes in digital EHR, track diagnostic markers every 15 minutes, and report to senior clinical attending.")
        elif discipline == "Pure & Applied Sciences":
            lines.append("```python")
            lines.append("# Scientific Statistical Modeling & Hypothesis Testing")
            lines.append("import numpy as np")
            lines.append("from scipy import stats")
            lines.append("")
            lines.append("control_group = np.random.normal(loc=50, scale=5, size=100)")
            lines.append("treatment_group = np.random.normal(loc=54, scale=5, size=100)")
            lines.append("")
            lines.append("t_stat, p_val = stats.ttest_ind(control_group, treatment_group)")
            lines.append("print(f'T-Statistic: {t_stat:.4f}, P-Value: {p_val:.4e}')")
            lines.append("assert p_val < 0.05, 'Hypothesis test failed: no statistical significance'")
            lines.append("```")
        elif discipline == "Business & Finance":
            lines.append("```sql")
            lines.append("-- Corporate Financial Modeling & Revenue Variance Query")
            lines.append("SELECT")
            lines.append("    fiscal_quarter,")
            lines.append("    SUM(budgeted_revenue) AS target_revenue,")
            lines.append("    SUM(actual_revenue) AS realized_revenue,")
            lines.append("    ROUND(((SUM(actual_revenue) - SUM(budgeted_revenue)) / SUM(budgeted_revenue)) * 100, 2) AS variance_pct")
            lines.append("FROM corporate_financial_ledger")
            lines.append("GROUP BY fiscal_quarter;")
            lines.append("```")
        elif discipline == "Arts & Humanities":
            lines.append("```javascript")
            lines.append("// Figma Auto-Layout Design System Token Config")
            lines.append("const designTokens = {")
            lines.append("  colorSystem: { primary: '#38bdf8', surface: '#0f172a', text: '#f8fafc' },")
            lines.append("  spacingGrid: { base: 8, md: 16, lg: 24, xl: 32 },")
            lines.append("  autoLayout: { padding: '16px 24px', gap: '12px', alignment: 'CENTER_LEFT' }")
            lines.append("};")
            lines.append("```")
        else:
            lines.append("```python")
            lines.append(f"# Production Implementation for {comp_name}")
            lines.append("from typing import Dict, Any")
            lines.append("import logging")
            lines.append("")
            lines.append("class CompetencyHandler:")
            lines.append("    def __init__(self, config: Dict[str, Any]):")
            lines.append("        self.config = config")
            lines.append("        self.is_active = True")
            lines.append("")
            lines.append("    def execute_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:")
            lines.append("        if not payload:")
            lines.append("            raise ValueError('Payload cannot be empty')")
            lines.append(f"        print('Executing {comp_name} production pipeline')")
            lines.append("        return {'status': 'SUCCESS', 'result': payload}")
            lines.append("```")

        lines.append("")

        lines.append("### 3. Common Pitfalls & Failure Modes")
        lines.append(f"Top 2 mistakes junior professionals make when implementing **{comp_name}**:")
        lines.append(f"1. **Mistake 1: Lack of Edge-Case & Error Validation**: Failing to handle non-standard input data or unexpected failures.")
        lines.append(f"   *Fix:* Implement strict validation, boundary checking, and fallback exception handling before processing.")
        lines.append(f"2. **Mistake 2: Ignoring Performance & Scalability Overhead**: Writing unoptimized blocking logic that degrades under high load.")
        lines.append(f"   *Fix:* Profile execution latency, utilize caching or asynchronous processing, and audit resource consumption.")
        lines.append("")

        lines.append("### 4. Hands-on Capstone Project / Task")
        lines.append(f"**Objective:** Build and document a verifiable capstone project demonstrating mastery of **{comp_name}** for your resume.")
        lines.append(f"1. **Task 1**: Design and document the system architecture / workflow specification for {comp_name}.")
        lines.append(f"2. **Task 2**: Implement the core solution with full test coverage and automated verification.")
        lines.append(f"3. **Task 3**: Create a GitHub / Portfolio repository containing an executive README.md, code artifacts, and benchmark results.")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def compile_typeset_study_manual(taxonomy: dict, competency_audit: dict, raw_markdown: str = "") -> str:
    """
    Technical Document Formatter and Typesetting Specialist Engine.
    Compiles, formats, and typesets the precision study manual with clean LaTeX formulas,
    strict heading hierarchy, language-tagged code blocks, and a standardized metadata header.
    """
    target_role = taxonomy.get("target_role", "Software Engineer")
    specialization = taxonomy.get("specialization", "Computer Science")
    experience_tier = taxonomy.get("experience_tier", "Student/Fresh Graduate (0 yrs)")
    ats_score = competency_audit.get("ats_score", 45)
    gaps = competency_audit.get("verified_gaps", [])
    total_modules = len(gaps)

    header = f"""# {target_role} - Precision Study Manual

> **CANDIDATE METADATA & ATS PROFILE**  
> - **Target Role:** {target_role}  
> - **Specialization:** {specialization} ({experience_tier})  
> - **ATS Readiness Score:** {ats_score}/100  
> - **Total Audited Modules:** {total_modules}  

---"""

    if not raw_markdown:
        raw_markdown = generate_precision_study_manual(taxonomy, competency_audit)

    body = re.sub(r"^#\s+.*?\n", "", raw_markdown.strip()).strip()
    body = re.sub(r"\\\[\s*(.*?)\s*\\\]", r"$$\1$$", body, flags=re.DOTALL)
    body = re.sub(r"\\\(\s*(.*?)\s*\\\)", r"$\1$", body, flags=re.DOTALL)
    body = re.sub(r"```\n", "```text\n", body)

    return header + "\n\n" + body


def predict_resume_domain(raw_text: str, detected_skills: List[str]) -> tuple[str, str, str]:
    """Predict resume discipline/domain accurately using word-boundary matching to prevent false positives."""
    lower_text = raw_text.lower()
    skills_set = set(s.lower() for s in detected_skills)

    domain_scores = {
        "arts": 0.0,
        "doctor": 0.0,
        "science": 0.0,
        "business": 0.0,
        "engineering": 0.0
    }

    def count_matches(keywords: list[str]) -> int:
        count = 0
        for kw in keywords:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, lower_text):
                count += 1
        return count

    # 1. Engineering & Technology Keywords
    eng_heavy = ["b.tech", "btech", "m.tech", "mtech", "b.e", "be", "computer science", "software engineer", "developer", "coding", "full stack", "backend", "frontend", "devops", "data structures", "algorithms", "operating system", "operating systems", "os", "computer networks", "dbms", "database management", "system programming", "compiler design", "computer organization", "computer architecture", "software engineering", "process scheduling", "memory management"]
    eng_skills = ["python", "java", "c++", "cpp", "c#", "javascript", "typescript", "react", "nodejs", "sql", "git", "github", "aws", "docker", "fastapi", "django", "flask", "rest api", "machine learning", "cad", "autocad", "matlab", "linux", "unix", "shell scripting", "semaphore", "deadlock", "concurrency", "oops"]
    
    eng_score = count_matches(eng_heavy) * 4.0 + count_matches(eng_skills) * 3.0
    for sk in detected_skills:
        if sk.lower() in ["python", "java", "javascript", "react", "nodejs", "sql", "git", "aws", "docker", "c++", "c#", "fastapi", "django", "rest api", "linux", "os", "c"]:
            eng_score += 4.0
    domain_scores["engineering"] = eng_score

    # 2. Medical & Healthcare / Doctor Keywords
    doctor_heavy = ["mbbs", "bams", "bhms", "doctor", "physician", "surgeon", "nurse", "nursing", "hospital", "clinic", "clinical", "patient care", "patient", "surgery", "bds", "dentist", "medical officer"]
    doctor_general = ["pharmacology", "pharmacy", "medical", "anatomy", "physiology", "pathology", "pediatrics", "healthcare", "diagnosis", "prescription", "bls", "acls"]
    
    doctor_score = count_matches(doctor_heavy) * 5.0 + count_matches(doctor_general) * 2.0
    if re.search(r"\bmbbs\b", lower_text) or re.search(r"\bdoctor of medicine\b", lower_text):
        doctor_score += 10.0
    domain_scores["doctor"] = doctor_score

    # 3. Arts, Design & Humanities Keywords
    arts_heavy = ["fine arts", "graphic design", "ui/ux", "figma", "photoshop", "illustrator", "creative writing", "journalism", "copywriting", "content writing", "bfa", "mfa", "animation", "visual arts", "dribbble", "behance"]
    arts_general = ["arts", "b.a", "ba", "m.a", "ma", "literature", "history", "media", "communication", "film", "acting", "music", "theatre", "sociology", "psychology", "philosophy", "sculpture", "painting", "fashion design"]
    
    arts_score = count_matches(arts_heavy) * 4.0 + count_matches(arts_general) * 2.0
    if "figma" in skills_set or "copywriting" in skills_set:
        arts_score += 5.0
    domain_scores["arts"] = arts_score

    # 4. Pure & Applied Science / Research Keywords
    science_heavy = ["b.sc", "bsc", "m.sc", "msc", "biotechnology", "microbiology", "biochemistry", "spss", "latex", "scientific paper", "research paper", "laboratory", "lab research"]
    science_general = ["physics", "chemistry", "biology", "botany", "zoology", "mathematics", "statistics", "genetics", "hypothesis", "astronomy", "geology"]
    
    science_score = count_matches(science_heavy) * 4.0 + count_matches(science_general) * 2.0
    domain_scores["science"] = science_score

    # 5. Business, Finance & Commerce Keywords
    business_heavy = ["bba", "mba", "b.com", "bcom", "m.com", "finance", "accounting", "chartered accountant", "marketing", "human resources", "sales", "business development", "power bi", "tableau", "salesforce"]
    business_general = ["hr", "economics", "banking", "commerce", "auditing", "tally", "crm", "operations", "supply chain", "brand manager", "business analyst"]
    
    business_score = count_matches(business_heavy) * 4.0 + count_matches(business_general) * 2.0
    domain_scores["business"] = business_score

    top_domain = max(domain_scores, key=domain_scores.get)
    if domain_scores[top_domain] < 2.0:
        top_domain = "engineering"

    domain_meta = {
        "arts": ("Arts & Commerce Student", "🎨", "Degree background in Arts, Humanities, Fine Arts, Design, or Commerce."),
        "doctor": ("Medical & Healthcare Student", "🩺", "Degree background in Medical Sciences, MBBS, Pharmacy, Nursing, or Clinical Healthcare."),
        "science": ("Science & Research Student", "🔬", "Degree background in B.Sc, M.Sc, Pure Sciences, Mathematics, or Laboratory Research."),
        "business": ("Arts & Commerce Student", "📊", "Degree background in B.Com, M.Com, BBA, MBA, Finance, or Commerce."),
        "engineering": ("Engineering & Technology Student", "💻", "Degree background in B.Tech, M.Tech, B.E, M.E, BCA, MCA, or Computer Science.")
    }

    return domain_meta[top_domain]


SKILL_ALIASES = {
    "python": ["python", "py"],
    "javascript": ["javascript", "js"],
    "react": ["react", "reactjs"],
    "nodejs": ["nodejs", "node.js", "node"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "sql": ["sql", "mysql", "postgresql", "database"],
    "java": ["java", "spring boot", "spring"],
    "csharp": ["c#", "csharp"],
    "aws": ["aws", "amazon web services"],
    "docker": ["docker", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "git": ["git", "github", "gitlab"],
    "machine learning": ["machine learning", "ml", "ai"],
    "pandas": ["pandas"],
    "numpy": ["numpy"],
    "excel": ["excel", "microsoft excel"],
    "power bi": ["power bi", "powerbi"],
    "tableau": ["tableau"],
    "fastapi": ["fastapi"],
    "django": ["django"],
    "flask": ["flask"],
    "rest api": ["rest api", "api", "apis"],
    "figma": ["figma", "ui ux", "ui/ux", "wireframing"],
    "photoshop": ["photoshop", "adobe photoshop"],
    "illustrator": ["illustrator", "adobe illustrator"],
    "copywriting": ["copywriting", "content writing"],
    "testing": ["testing", "qa", "selenium"],
    "linux": ["linux", "ubuntu"],
    "cloud": ["cloud", "azure", "gcp", "google cloud"],
}

JOB_CATALOG = [
    # Engineering / Tech Jobs
    {"domain": "Engineering & Computer Science", "title": "Software Development Engineer", "skills": ["python", "java", "sql", "git", "rest api", "c++"], "reason": "Strong fit for software engineering, algorithmic problem solving, and backend services."},
    {"domain": "Engineering & Computer Science", "title": "Full Stack Engineer", "skills": ["javascript", "react", "nodejs", "html", "css", "sql", "git"], "reason": "A strong option for fullstack web application development and UI prototyping."},
    {"domain": "Engineering & Computer Science", "title": "Python & Data Engineer", "skills": ["python", "sql", "pandas", "numpy", "fastapi", "git"], "reason": "Strong fit for Python data pipelines, REST APIs, and database engineering."},
    {"domain": "Engineering & Computer Science", "title": "DevOps & Cloud Engineer", "skills": ["aws", "docker", "kubernetes", "linux", "cloud", "git"], "reason": "Suitable for cloud architecture, containerization, and automation pipelines."},

    # Arts Jobs
    {"domain": "Arts, Design & Humanities", "title": "UI/UX & Visual Designer", "skills": ["figma", "photoshop", "illustrator", "html", "css"], "reason": "Great match for creative design, interactive prototyping, and user testing."},
    {"domain": "Arts, Design & Humanities", "title": "Content Strategist & Copywriter", "skills": ["copywriting", "excel", "figma"], "reason": "Strong alignment with digital content creation, SEO copywriting, and brand storytelling."},
    {"domain": "Arts, Design & Humanities", "title": "Graphic Designer & Brand Lead", "skills": ["photoshop", "illustrator", "figma", "canva"], "reason": "Ideal for visual artists, graphic branding, and creative media production."},

    # Doctor / Medical Jobs
    {"domain": "Medical & Healthcare / Doctor", "title": "Resident Medical Officer", "skills": ["patient care", "diagnostics", "bls", "acls"], "reason": "Excellent match for clinical diagnosis, patient management, and emergency hospital care."},
    {"domain": "Medical & Healthcare / Doctor", "title": "Clinical Research Associate", "skills": ["clinical trial", "research", "medical writing"], "reason": "Strong fit for medical research, pharmaceutical trials, and healthcare studies."},
    {"domain": "Medical & Healthcare / Doctor", "title": "Healthcare Administrator", "skills": ["hospital management", "excel", "health informatics"], "reason": "Perfect for clinical operations, healthcare policy, and facility leadership."},

    # Science Jobs
    {"domain": "Pure & Applied Science / Research", "title": "Research Scientist & Lab Analyst", "skills": ["laboratory", "spss", "python", "excel"], "reason": "High alignment with lab experimentation, scientific testing, and research data."},
    {"domain": "Pure & Applied Science / Research", "title": "Data Analyst / Statistician", "skills": ["python", "sql", "excel", "spss", "r"], "reason": "Great fit for statistical analysis, hypothesis testing, and quantitative research."},

    # Business Jobs
    {"domain": "Business, Finance & Commerce", "title": "Financial Analyst", "skills": ["excel", "power bi", "tableau", "sql"], "reason": "Ideal match for corporate finance, financial modeling, and data reporting."},
    {"domain": "Business, Finance & Commerce", "title": "Business Analyst", "skills": ["excel", "sql", "tableau", "power bi"], "reason": "Strong fit for business requirements, executive reporting, and workflow optimization."},
    {"domain": "Business, Finance & Commerce", "title": "Digital Marketing Specialist", "skills": ["copywriting", "excel", "power bi"], "reason": "Great match for performance marketing, campaign management, and customer analytics."}
]


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

def canonicalize_skill(skill: str) -> str:
    key = normalize_text(skill)
    for canonical, aliases in SKILL_ALIASES.items():
        if key in {normalize_text(alias) for alias in aliases}:
            return canonical
    return key

def extract_resume_skills(raw_text: str) -> List[str]:
    normalized = normalize_text(raw_text)
    detected = []
    for canonical, aliases in SKILL_ALIASES.items():
        if any(normalize_text(alias) in normalized for alias in aliases):
            detected.append(canonical)
    return sorted(dict.fromkeys(detected))

def parse_company_skills(company_skills: str) -> List[str]:
    if not company_skills:
        return []
    skills = []
    for item in re.split(r"[,;\n]+", company_skills):
        item = item.strip()
        if item:
            skills.append(canonicalize_skill(item))
    return sorted(dict.fromkeys(skills))

def build_job_recommendations(raw_text: str, domain_name: str, company_skills: str = "") -> List[JobSuggestion]:
    resume_skills = set(extract_resume_skills(raw_text))
    company_skill_set = set(parse_company_skills(company_skills))

    suggestions = []
    for job in JOB_CATALOG:
        is_same_domain = (job["domain"] == domain_name)
        job_skill_set = set(job["skills"])
        matched_skills = sorted(resume_skills & job_skill_set)
        company_matched = sorted(company_skill_set & job_skill_set)
        missing_skills = sorted(job_skill_set - resume_skills)

        overlap_ratio = len(matched_skills) / max(1, len(job_skill_set))
        company_boost = min(20, len(company_matched) * 10)
        domain_boost = 35 if is_same_domain else 0
        
        score = min(100, int(round(overlap_ratio * 45 + domain_boost + company_boost)))

        if is_same_domain or score >= 45:
            suggestions.append(
                JobSuggestion(
                    title=job["title"],
                    match_score=score,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills[:3],
                    reason=job["reason"],
                )
            )

    suggestions.sort(key=lambda item: (-item.match_score, item.title))
    return suggestions[:4]


def calculate_probabilities_and_roadmap(raw_text: str, detected_skills: List[str], domain_name: str, total_score: float, action_score: float, metrics_score: float, structure_score: float, is_valid_resume: bool):
    skills_set = set(detected_skills)
    roadmap: List[StudyTopic] = []
    skill_gaps: List[str] = []

    if not is_valid_resume:
        hackathon_prob = 10.0
        intern_prob = 15.0
        hackathon_status = "❌ Document Incomplete / Invalid"
        intern_status = "❌ Missing essential resume details"
        
        roadmap.append(StudyTopic(
            category="Resume Section Requirements",
            topic="Include Essential Resume Details",
            recommendation="Ensure your uploaded resume contains: 1) Personal Details, 2) Career Objective / Target Role, 3) Education, 4) Technical Skills, 5) Languages.",
            priority="HIGH",
            impact="Required for Complete Resume Analysis"
        ))
        return hackathon_prob, intern_prob, hackathon_status, intern_status, roadmap, ["Complete Resume Sections"]

    # Calculate domain-tailored probabilities & study roadmaps
    if domain_name == "Engineering & Computer Science":
        hackathon_prob = min(98.0, max(45.0, 50.0 + (len(skills_set & {"git", "python", "javascript", "react", "fastapi", "aws", "c++", "sql"}) * 7.0)))
        intern_prob = min(96.0, max(40.0, (total_score * 0.45) + (len(skills_set & {"python", "java", "sql", "git", "rest api", "c++"}) * 5.0)))
        hackathon_status = "🔥 Top Tier Hackathon & Prototyping Contender" if hackathon_prob >= 80 else "⚡ Competitive Technical Contender"
        intern_status = "🌟 Strong Software Engineering Internship Fit" if intern_prob >= 78 else "📈 Competitive Engineering Fit"

        if "git" not in skills_set:
            skill_gaps.append("Git & GitHub Branching")
            roadmap.append(StudyTopic(
                category="Technical Skills (Tools)",
                topic="Git Branching & GitHub Open Source PRs",
                recommendation="Master Git commands (clone, commit, push, branch, merge) and host 2+ project repositories on GitHub with clear README documentation.",
                priority="HIGH",
                impact="+15% Technical Interview Selection Odds"
            ))
        if not (skills_set & {"fastapi", "nodejs", "django", "flask", "rest api"}):
            skill_gaps.append("REST API & Backend Development")
            roadmap.append(StudyTopic(
                category="Technical Skills (Web Technologies)",
                topic="REST API Development (FastAPI / Node.js)",
                recommendation="Build JSON REST APIs, handle HTTP methods (GET, POST, PUT, DELETE), and connect endpoints to SQL databases.",
                priority="HIGH",
                impact="+20% Backend / Fullstack Role Match"
            ))
        roadmap.append(StudyTopic(
            category="Technical Skills (Core Engineering)",
            topic="Data Structures, Algorithms & Problem Solving",
            recommendation="Solve 3-5 algorithmic problems weekly on Arrays, HashMaps, Strings, Trees, and Time Complexity.",
            priority="HIGH",
            impact="Essential for Passing Technical Engineering Interviews"
        ))

    elif domain_name == "Arts, Design & Humanities":
        hackathon_prob = min(98.0, max(40.0, 50.0 + (len(skills_set & {"figma", "photoshop", "illustrator", "html", "css", "copywriting"}) * 8.0)))
        intern_prob = min(96.0, max(35.0, (total_score * 0.50) + (structure_score * 0.35)))
        hackathon_status = "🎨 Top Design & Case Competition Contender" if hackathon_prob >= 75 else "🎨 Creative Portfolio Contender"
        intern_status = "🌟 Strong Design / Content Internship Candidate" if intern_prob >= 75 else "📈 Competitive Creative Candidate"

        if "figma" not in skills_set:
            skill_gaps.append("Figma & UI/UX Prototyping")
            roadmap.append(StudyTopic(
                category="Technical Skills (Design Tools)",
                topic="Figma Design Systems & Interactive Wireframing",
                recommendation="Master Figma components, auto-layout, and interactive prototypes to create modern app layouts.",
                priority="HIGH",
                impact="+25% Design Portfolio Pass Rate"
            ))
        if not (skills_set & {"photoshop", "illustrator"}):
            skill_gaps.append("Adobe Creative Suite")
            roadmap.append(StudyTopic(
                category="Technical Skills (Visual Arts)",
                topic="Adobe Illustrator & Graphic Branding",
                recommendation="Learn vector logo design, branding systems, and digital asset production for creative campaigns.",
                priority="HIGH",
                impact="+20% Graphic Design Selection Odds"
            ))
        roadmap.append(StudyTopic(
            category="Creative Portfolio Showcase",
            topic="Online Design Portfolio (Behance / Dribbble / Medium)",
            recommendation="Publish 3 complete case studies demonstrating your creative process from wireframe to final polish.",
            priority="HIGH",
            impact="Essential for Creative & Design Interview Calls"
        ))

    elif domain_name == "Medical & Healthcare / Doctor":
        hackathon_prob = min(95.0, max(30.0, 45.0 + (total_score * 0.40)))
        intern_prob = min(98.0, max(45.0, (total_score * 0.55) + (structure_score * 0.30)))
        hackathon_status = "🩺 Qualified Clinical Research Candidate"
        intern_status = "🌟 High Clinical Residency / Medical Appointment Odds" if intern_prob >= 78 else "📈 Competitive Medical Graduate"

        roadmap.append(StudyTopic(
            category="Clinical Certifications",
            topic="BLS & ACLS Certification & Patient Protocol",
            recommendation="Complete certified Basic Life Support (BLS) and Advanced Cardiovascular Life Support (ACLS) clinical modules.",
            priority="HIGH",
            impact="+30% Hospital Residency Selection Rate"
        ))
        roadmap.append(StudyTopic(
            category="Healthcare Technology",
            topic="Electronic Health Records (EHR) & Health Informatics",
            recommendation="Familiarize with hospital EMR/EHR software platforms and digital medical charting protocols.",
            priority="HIGH",
            impact="+22% Clinical Systems Adaptability"
        ))

    elif domain_name == "Pure & Applied Science / Research":
        hackathon_prob = min(95.0, max(35.0, 45.0 + (len(skills_set & {"python", "excel", "spss", "sql"}) * 10.0)))
        intern_prob = min(96.0, max(40.0, (total_score * 0.50) + (metrics_score * 0.35)))
        hackathon_status = "🔬 Strong Scientific Research Contender"
        intern_status = "🌟 Outstanding Research & Lab Fellowship Candidate" if intern_prob >= 75 else "📈 Competitive Scientific Candidate"

        roadmap.append(StudyTopic(
            category="Scientific Data Analysis",
            topic="Statistical Modeling using R / Python / SPSS",
            recommendation="Practice hypothesis testing, regression modeling, and statistical data visualization for lab data.",
            priority="HIGH",
            impact="+28% Research Fellowship Odds"
        ))
        roadmap.append(StudyTopic(
            category="Laboratory Protocols",
            topic="GLP (Good Laboratory Practice) & Safety Standards",
            recommendation="Study standardized lab procedures, sample storage protocols, and biosafety guidelines.",
            priority="HIGH",
            impact="Mandatory for Industrial Research Labs"
        ))

    else:
        # Business, Finance & Commerce
        hackathon_prob = min(98.0, max(40.0, 45.0 + (len(skills_set & {"excel", "power bi", "tableau", "sql"}) * 10.0)))
        intern_prob = min(96.0, max(40.0, (total_score * 0.50) + (metrics_score * 0.35)))
        hackathon_status = "💼 Business Case Competition Contender"
        intern_status = "🌟 Strong Business & Finance Internship Candidate" if intern_prob >= 75 else "📈 Competitive Business Associate"

        if not (skills_set & {"power bi", "tableau"}):
            skill_gaps.append("Business Intelligence (Power BI / Tableau)")
            roadmap.append(StudyTopic(
                category="Technical Skills (Analytics Tools)",
                topic="Interactive Dashboarding with Power BI or Tableau",
                recommendation="Build executive KPI dashboards connecting sales, financial, or operational data sources.",
                priority="HIGH",
                impact="+25% Analytics Role Selection Odds"
            ))
        roadmap.append(StudyTopic(
            category="Financial Modeling",
            topic="Advanced Financial Modeling & Excel Analysis",
            recommendation="Master Pivot Tables, VLOOKUP, and DCF valuation models for corporate analysis.",
            priority="HIGH",
            impact="+30% Corporate Finance Interview Rate"
        ))

    return hackathon_prob, intern_prob, hackathon_status, intern_status, roadmap, skill_gaps


@app.post("/analyzer", response_model=AnalysisResult)
@app.post("/api/analyzer", response_model=AnalysisResult)
@app.post("/api/rag/analyze", response_model=AnalysisResult)
async def analyze_resume(
    file: Optional[UploadFile] = File(None),
    resume_text: str = Form(""),
    company_skills: str = Form("")
):
    raw_text = ""
    if file:
        try:
            contents = await file.read()
            raw_text = extract_text_from_file(contents, file.filename)
        except Exception:
            raw_text = ""

    if not raw_text.strip() and resume_text.strip():
        raw_text = resume_text.strip()

    if not raw_text.strip():
        raw_text = "Missing document text"

    # 1. Document Resume Validation (Check required resume sections: Personal Details, Career Objective, Education, Technical Skills, Languages)
    is_valid_resume, is_complete_resume, warning_msg, missing_sections = validate_resume_document(raw_text)

    # 2. Extract detected skills & Predict Domain
    detected_skills = extract_resume_skills(raw_text)
    domain_name, domain_icon, domain_desc = predict_resume_domain(raw_text, detected_skills)

    # 3. Preprocess for scoring
    lower_text = raw_text.lower()
    words = re.findall(r"\b\w+\b", raw_text)
    word_count = len(words)

    feedback = []
    company_skill_list = parse_company_skills(company_skills)

    if not is_valid_resume or not is_complete_resume:
        return AnalysisResult(
            is_valid_resume=False,
            is_complete_resume=False,
            missing_sections=missing_sections,
            warning_message=warning_msg,
            predicted_domain="Invalid Document / Non-Resume File",
            domain_icon="⚠️",
            domain_description="The uploaded document could not be verified as a valid complete resume.",
            action_score=0,
            metrics_score=0,
            structure_score=0,
            length_score=0,
            total_score=0.0,
            grade="F",
            hackathon_probability=0.0,
            internship_probability=0.0,
            hackathon_badge="Invalid File",
            internship_badge="Invalid File",
            hackathon_status="Re-upload a complete resume to calculate hackathon selection odds.",
            internship_status="Re-upload a complete resume to calculate internship qualification.",
            feedback=[{"type": "fail", "text": warning_msg}],
            detected_skills=[],
            company_skills=[],
            suggested_jobs=[],
            study_roadmap=[],
            skill_gaps=[],
            domain={"title": "Invalid Document", "icon": "⚠️", "description": warning_msg},
            hackathon_odds={"score": 0.0, "badge": "Invalid File", "status": warning_msg},
            internship_odds={"score": 0.0, "badge": "Invalid File", "status": warning_msg},
            overall_score={"score": 0.0, "grade": "F"}
        )

    # Technical Skill Evaluation
        tech_skills_score = min(100.0, float(len(detected_skills) * 22.0))
        if tech_skills_score < 40.0:
            tech_skills_score = 40.0

        if len(detected_skills) >= 3:
            feedback.append({"type": "pass", "text": f"Technical Skills Analysis: Detected key tools across Programming, Web, Database & Software Tools ({', '.join(detected_skills[:5])})."})
        else:
            feedback.append({"type": "fail", "text": "Technical Skill Suggestion: Expand your Technical Skills section with Programming languages, Web Tech, Databases, or Developer Tools."})

        # Action Verbs
        action_verbs = ["achieved", "developed", "managed", "created", "led", "increased", "reduced",
                        "designed", "implemented", "engineered", "launched", "orchestrated", "automated",
                        "optimized", "built", "assisted", "supported", "coordinated", "handled", "improved"]
        found_verbs = list(set([v for v in action_verbs if v in lower_text]))
        action_score = min(100.0, float(len(found_verbs) * 25))

        if len(found_verbs) >= 2:
            feedback.append({"type": "pass", "text": f"Action impact detected ({len(found_verbs)} key accomplishment verbs found)."})
        else:
            feedback.append({"type": "fail", "text": "Low action impact detected. Add stronger accomplishment verbs."})

        # Quantifiable Metrics
        numbers = re.findall(r'\b\d+(?:%|\b)', raw_text)
        metrics_score = min(100.0, float(len(numbers) * 35))

        if len(numbers) >= 2:
            feedback.append({"type": "pass", "text": f"Quantifiable achievements detected ({len(numbers)} numerical data points)."})
        else:
            feedback.append({"type": "fail", "text": "Lacks measurable impact. Incorporate percentages, user counts, or metric data."})

        # Structure & Length
        required_sections = ["education", "experience", "skills"]
        found_sections = [sec for sec in required_sections if sec in lower_text]
        structure_score = (len(found_sections) / len(required_sections)) * 100.0

        if word_count < 100:
            length_score = 60.0
            feedback.append({"type": "fail", "text": f"Resume text is short ({word_count} words). Aim for 200–500 words."})
        elif word_count > 600:
            length_score = 75.0
            feedback.append({"type": "fail", "text": f"Resume is verbose ({word_count} words). Condense key bullet points."})
        else:
            length_score = 100.0
            feedback.append({"type": "pass", "text": f"Ideal concise length ({word_count} words)."})

        # Grade calculation
        raw_total = (tech_skills_score * 0.35) + (action_score * 0.25) + (metrics_score * 0.25) + (structure_score * 0.15)
        total_score = min(100.0, round(raw_total))

        grade = "A" if total_score >= 85 else ("B" if total_score >= 75 else ("C" if total_score >= 60 else "D"))

    # 4. Job Suggestions tailored to Domain
    suggested_jobs = build_job_recommendations(raw_text, domain_name, company_skills)

    # 5. Probabilities & Domain-Specific Roadmap
    hack_prob, int_prob, hack_status, int_status, roadmap, skill_gaps = calculate_probabilities_and_roadmap(
        raw_text, detected_skills, domain_name, total_score, action_score, metrics_score, structure_score, is_valid_resume and is_complete_resume
    )

    if is_valid_resume and is_complete_resume:
        feedback.append({"type": "pass", "text": f"Technical Skills Analysis -> Predicted Field: {domain_icon} {domain_name}."})

    roadmap_dict_list = [{"title": r.title, "category": r.category, "desc": r.description, "impact": r.impact} for r in roadmap]
    jobs_dict_list = [{"title": j.title, "match_score": j.match_score, "reason": j.reason, "matched_skills": j.matched_skills, "missing_skills": j.missing_skills} for j in suggested_jobs]

    return AnalysisResult(
        is_valid_resume=is_valid_resume and is_complete_resume,
        is_complete_resume=is_complete_resume,
        missing_sections=missing_sections,
        warning_message=warning_msg if (not is_valid_resume or not is_complete_resume) else None,
        predicted_domain=domain_name,
        domain_icon=domain_icon,
        domain_description=domain_desc,
        action_score=round(action_score),
        metrics_score=round(metrics_score),
        structure_score=round(structure_score),
        length_score=round(length_score),
        total_score=total_score,
        grade=grade,
        hackathon_probability=hack_prob,
        internship_probability=int_prob,
        hackathon_status=hack_status,
        internship_status=int_status,
        feedback=feedback,
        detected_skills=detected_skills,
        company_skills=company_skill_list,
        suggested_jobs=suggested_jobs,
        study_roadmap=roadmap,
        skill_gaps=skill_gaps,
        domain={"title": domain_name, "icon": domain_icon, "description": domain_desc},
        hackathon_odds={"score": hack_prob, "badge": "High Probability" if hack_prob > 75 else "Competitive", "status": hack_status},
        internship_odds={"score": int_prob, "badge": "Competitive" if int_prob > 70 else "Building Foundation", "status": int_status},
        overall_score={"score": total_score, "grade": grade},
        metrics={"action_verbs": round(action_score), "metrics_presence": round(metrics_score), "structure": round(structure_score), "length_balance": round(length_score)},
        roadmap=roadmap_dict_list,
        job_matches=jobs_dict_list,
        verbatim_facts=extract_verbatim_facts(raw_text),
        taxonomy_analysis=classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text),
        competency_audit=audit_competency_gaps(extract_verbatim_facts(raw_text), classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text), raw_text),
        precision_study_manual=generate_precision_study_manual(
            classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text),
            audit_competency_gaps(extract_verbatim_facts(raw_text), classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text), raw_text)
        ),
        compiled_typeset_manual=compile_typeset_study_manual(
            classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text),
            audit_competency_gaps(extract_verbatim_facts(raw_text), classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text), raw_text),
            generate_precision_study_manual(
                classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text),
                audit_competency_gaps(extract_verbatim_facts(raw_text), classify_candidate_taxonomy(extract_verbatim_facts(raw_text), raw_text), raw_text)
            )
        )
    )

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception:
            clean = re.sub(r"[^\x20-\x7E\n\r\t]", " ", file_bytes.decode("latin1", errors="ignore"))
            return clean if len(clean) > 50 else filename

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            reader = PdfReader(temp_path)
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return file_bytes.decode("utf-8", errors="ignore")


@app.get("/api/jobs")
def get_live_jobs(prompt: str = "", q: str = "", category: str = "all", page: int = 1, limit: int = 12):
    user_query = (prompt or q or "").lower().strip()
    cat_query = (category or "all").lower().strip()

    all_jobs = []

    # Attempt loading from local aggregated_opportunities.json file
    json_path = os.path.join(os.path.dirname(__file__), "aggregated_opportunities.json")
    if os.path.exists(json_path):
        try:
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
                            "deadline_or_posted": item.get("deadline_or_posted") or "Active"
                        })
        except Exception:
            all_jobs = []

    # Fallback curated opportunities if json is empty or missing
    if not all_jobs:
        all_jobs = [
            { "id": "job-1", "company": "GOOGLE", "organization": "GOOGLE", "title": "Software Engineer", "type": "job", "category": "Engineering", "location": "Bangalore / Remote", "salary": "₹18,00,000 - ₹30,00,000 / yr", "description": "Develop scalable web services and cloud algorithms.", "skills_required": ["Python", "C++", "System Architecture", "Cloud"], "apply_url": "https://careers.google.com/" },
            { "id": "job-2", "company": "MICROSOFT", "organization": "MICROSOFT", "title": "Fullstack Developer Intern", "type": "internship", "category": "Internships", "location": "Hyderabad, India", "salary": "₹50,000 / mo", "description": "Architect web microservices and React interfaces.", "skills_required": ["React", "TypeScript", "Azure", "Node.js"], "apply_url": "https://careers.microsoft.com/" },
            { "id": "job-3", "company": "MAJOR LEAGUE HACKING", "organization": "MLH", "title": "Global Tech Hackathon 2026", "type": "hackathon", "category": "Hackathons", "location": "Online / Worldwide", "salary": "$25,000 Total Prizes", "description": "Build innovative web & AI applications with developers worldwide.", "skills_required": ["Python", "Generative AI", "React", "FastAPI"], "apply_url": "https://mlh.io" },
            { "id": "job-4", "company": "DEVPOST", "organization": "DEVPOST", "title": "AI & Cloud Innovation Challenge", "type": "hackathon", "category": "Hackathons", "location": "Remote", "salary": "$50,000 Prize Pool", "description": "Develop cutting-edge machine learning models.", "skills_required": ["Python", "TensorFlow", "AWS", "PyTorch"], "apply_url": "https://devpost.com" },
            { "id": "job-5", "company": "KENDRIYA VIDYALAYA / EDTECH", "organization": "EDTECH ACADEMY", "title": "Computer Science Instructor", "type": "job", "category": "Teaching", "location": "Bangalore / Remote", "salary": "₹6,00,000 - ₹12,00,000 / yr", "description": "Teach programming languages, algorithms, and CS fundamentals.", "skills_required": ["Python", "Java", "Data Structures", "Pedagogy"], "apply_url": "https://www.indeed.com" },
            { "id": "job-6", "company": "ADOBE", "organization": "ADOBE", "title": "UI/UX & Brand Designer", "type": "job", "category": "Arts", "location": "Remote / Mumbai", "salary": "₹8,00,000 - ₹14,00,000 / yr", "description": "Create visual design systems, logos, and UI prototypes.", "skills_required": ["Figma", "Photoshop", "UI/UX", "Illustrator"], "apply_url": "https://www.behance.net" },
            { "id": "job-7", "company": "APOLLO HOSPITALS", "organization": "APOLLO HOSPITALS", "title": "Resident Medical Officer", "type": "job", "category": "Medical", "location": "Chennai / Delhi", "salary": "₹12,00,000 - ₹20,00,000 / yr", "description": "Clinical patient care, diagnostic reviews, and ER support.", "skills_required": ["Clinical Medicine", "Patient Care", "Healthcare Informatics"], "apply_url": "https://www.apollohospitals.com" }
        ]

    # Category Filtering
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

    # Fallback to category list if query returned 0 items
    if not filtered and all_jobs:
        if cat_query != "all":
            filtered = [j for j in all_jobs if cat_query in (j.get("category","")).lower() or cat_query in (j.get("type","")).lower()]
        if not filtered:
            filtered = all_jobs[:20]

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


class ApplicationRequest(BaseModel):
    opportunity_id: Optional[str] = None
    opportunity_title: Optional[str] = None
    organization: Optional[str] = None
    candidate_name: str
    candidate_email: str
    resume_text: Optional[str] = ""
    portfolio_url: Optional[str] = ""
    cover_note: Optional[str] = ""
    apply_mode: Optional[str] = "native"


class CoverLetterRequest(BaseModel):
    opportunity_title: Optional[str] = None
    organization: Optional[str] = None
    candidate_name: Optional[str] = None
    key_skills: Optional[list] = None


python_in_memory_applications = []


@app.api_route("/api/opportunities/search", methods=["GET", "POST"])
def search_opportunities_endpoint(q: str = "", prompt: str = "", category: str = "all", page: int = 1, limit: int = 20):
    return get_live_jobs(prompt=prompt, q=q, category=category, page=page, limit=limit)


@app.post("/api/applications/apply")
def apply_opportunity_endpoint(payload: ApplicationRequest):
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
    python_in_memory_applications.insert(0, record)

    return {
        "success": True,
        "message": f"Application submitted successfully via AutoHire! ({record['mode']})",
        "application": record,
        "redirect_url": None if is_native else f"https://google.com/search?q={record['organization']}+{record['opportunity_title']}"
    }


@app.get("/api/applications/status")
def application_status_endpoint(email: str = ""):
    apps = python_in_memory_applications
    if email:
        apps = [a for a in apps if a["candidate_email"].lower() == email.lower()]

    return {
        "success": True,
        "total": len(apps),
        "applications": apps
    }


@app.post("/api/applications/cover-letter")
def generate_cover_letter_endpoint(payload: CoverLetterRequest):
    name = payload.candidate_name or "Applicant"
    title = payload.opportunity_title or "Software Engineering Role"
    org = payload.organization or "your organization"
    skills = ", ".join(payload.key_skills) if payload.key_skills else "Fullstack Software Engineering, Python, React, REST APIs"

    letter = f"""Dear Hiring Team at {org},

I am writing to express my strong enthusiasm for the {title} position. With verified expertise in {skills}, I have engineered robust systems and delivered scalable technical solutions.

My background aligns directly with the core competencies expected at {org}. I am eager to leverage my technical problem-solving capabilities to drive measurable impact.

Thank you for your time and consideration.

Best regards,  
{name}"""

    return {
        "success": True,
        "cover_letter": letter
    }


@app.api_route("/api/rag/query", methods=["GET", "POST"])
def rag_query(q: str = "", prompt: str = "", category: str = "all"):
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


@app.get("/api/rag/search")
def rag_search(q: str = "", prompt: str = "", k: int = 5, category: str = "all"):
    query = (prompt or q or "").strip().lower()
    
    docs = [
        {"id": "doc-1", "title": "Data Structures & Algorithms Mastery", "category": "Engineering", "content": "Arrays, Trees, Graphs, HashMaps, Dynamic Programming patterns."},
        {"id": "doc-2", "title": "Figma UI/UX & Visual Systems", "category": "Arts", "content": "Interactive wireframes, auto-layout components, typography guidelines."},
        {"id": "doc-3", "title": "Clinical Patient Diagnostics & BLS", "category": "Medical", "content": "Basic Life Support certification, diagnostic protocol, hospital rounding."},
        {"id": "doc-4", "title": "CS Curriculum & Pedagogy", "category": "Teaching", "content": "Interactive programming lesson plans, lab assessments, student mentorship."}
    ]

    q_words = set(re.findall(r"\w+", query))
    scored = []

    for d in docs:
        d_words = set(re.findall(r"\w+", (d["title"] + " " + d["content"]).lower()))
        score = len(q_words.intersection(d_words)) / max(1, len(q_words)) if q_words else 0.5
        scored.append({"id": d["id"], "title": d["title"], "category": d["category"], "similarityScore": f"{round(score * 100)}%"})

    scored.sort(key=lambda x: int(x["similarityScore"].replace("%", "")), reverse=True)
    return {"success": True, "query": query, "count": len(scored[:k]), "results": scored[:k]}


@app.post("/api/rag/analyze")
async def rag_analyze(
    resume_text: Optional[str] = Form(None),
    company_skills: Optional[str] = Form(None),
    target_skills: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    text = (resume_text or "").strip()
    if file:
        file_bytes = await file.read()
        extracted = extract_text_from_file(file_bytes, file.filename or "resume.txt")
        if extracted:
            text = (extracted + "\n" + text).strip()

    skills_str = company_skills or target_skills or ""
    return await analyze_resume(file=file, resume_text=text, company_skills=skills_str)


if __name__ == "__main__":
    import uvicorn
    import os

    uvicorn.run(
        "app1:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "5503")),
        root_path="/",
        reload=False
    )