import os
import re
import tempfile
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import FileResponse

app = FastAPI(title="AutoHire RAG AI Resume Analyzer API")

@app.get("/")
async def home():
    return FileResponse("analyzer.html")

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


def validate_resume_document(raw_text: str) -> tuple[bool, bool, str, list[str]]:
    """
    Detect if the uploaded text is a complete resume containing all 5 required section categories:
    1. Personal Details (Name, Phone, Email, Location, LinkedIn, GitHub, Portfolio)
    2. Career Objective / Target Role (Target Job Role, Career Objective)
    3. Education (Degree/Course, Specialization, College, University, CGPA/Percentage, Year)
    4. Technical Skills (Programming, Web Technologies, Database, Tools/Software, Other Technical Skills)
    5. Languages (Languages known / Spoken languages)
    """
    lower_text = raw_text.lower()
    words = re.findall(r"\b\w+\b", raw_text)
    word_count = len(words)

    # 1. Timetable / Schedule / Non-resume keywords
    timetable_keywords = [
        "timetable", "time table", "class schedule", "lecture schedule", "period 1", "period 2", "period 3",
        "period 4", "period 5", "room no", "subject code", "course code", "exam schedule", "date sheet",
        "hall ticket", "semester schedule", "lecture time", "daily routine", "invoice", "receipt", "bill",
        "menu card", "syllabus sheet"
    ]
    timetable_hits = [kw for kw in timetable_keywords if kw in lower_text]
    if len(timetable_hits) >= 2 or (len(timetable_hits) >= 1 and word_count < 120):
        return False, False, "this is not an complete resume", ["Timetable/Non-resume file detected"]

    missing_sections = []

    # Check Section 1: PERSONAL DETAILS (Name, Phone, Email, Location, LinkedIn, GitHub, Portfolio)
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)) or "email" in lower_text
    has_phone = bool(re.search(r"\+?\d[\d\s-]{7,}", raw_text)) or any(k in lower_text for k in ["phone", "mobile", "contact", "call"])
    has_personal_meta = any(k in lower_text for k in ["linkedin", "github", "portfolio", "location", "address", "city", "state", "pincode", "name"])
    if not (has_email or has_phone or has_personal_meta):
        missing_sections.append("Personal Details (Name, Phone, Email, Location, LinkedIn, GitHub, Portfolio)")

    # Check Section 2: CAREER OBJECTIVE / TARGET ROLE
    objective_anchors = [
        "objective", "target role", "target job role", "career objective", "profile summary",
        "professional summary", "summary", "career goal", "about me", "seeking role", "seeking a role", "aspiring"
    ]
    if not any(anchor in lower_text for anchor in objective_anchors):
        missing_sections.append("Career Objective / Target Role")

    # Check Section 3: EDUCATION
    education_anchors = [
        "education", "degree", "course", "specialization", "college", "university", "school", "academic",
        "b.tech", "btech", "m.tech", "mtech", "b.e", "be", "b.sc", "bsc", "m.sc", "msc",
        "bba", "mba", "b.com", "bcom", "bca", "mca", "diploma", "10th", "12th",
        "cgpa", "gpa", "percentage", "year"
    ]
    if not any(anchor in lower_text for anchor in education_anchors):
        missing_sections.append("Education (Degree, Course, Specialization, College, University, CGPA, Year)")

    # Check Section 4: TECHNICAL SKILLS
    skills_anchors = [
        "skills", "technical skills", "programming", "web technologies", "database",
        "tools", "software", "technologies", "tech stack", "python", "javascript",
        "java", "c++", "c#", "html", "css", "sql", "react", "nodejs", "git", "aws", "excel", "power bi"
    ]
    if not any(anchor in lower_text for anchor in skills_anchors):
        missing_sections.append("Technical Skills (Programming, Web, Database, Tools)")

    # Check Section 5: LANGUAGES
    languages_anchors = [
        "languages", "language", "languages known", "mother tongue", "spoken languages",
        "english", "hindi", "tamil", "telugu", "kannada", "malayalam", "marathi", "bengali",
        "gujarati", "spanish", "french", "german", "japanese", "mandarin", "chinese", "russian"
    ]
    if not any(anchor in lower_text for anchor in languages_anchors):
        missing_sections.append("Languages")

    if word_count < 10:
        return False, False, "Please provide more resume text for analysis.", missing_sections

    return True, True, "", missing_sections


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
    eng_heavy = ["b.tech", "btech", "m.tech", "mtech", "b.e", "be", "computer science", "software engineer", "developer", "coding", "full stack", "backend", "frontend", "devops", "data structures", "algorithms"]
    eng_skills = ["python", "java", "c++", "c#", "javascript", "typescript", "react", "nodejs", "sql", "git", "github", "aws", "docker", "fastapi", "django", "flask", "rest api", "machine learning", "cad", "autocad", "matlab"]
    
    eng_score = count_matches(eng_heavy) * 4.0 + count_matches(eng_skills) * 3.0
    for sk in detected_skills:
        if sk.lower() in ["python", "java", "javascript", "react", "nodejs", "sql", "git", "aws", "docker", "c++", "c#", "fastapi", "django", "rest api"]:
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
        "arts": ("Arts, Design & Humanities", "🎨", "Focused on creative arts, visual design, media, copywriting, UI/UX, and literature."),
        "doctor": ("Medical & Healthcare / Doctor", "🩺", "Focused on clinical medicine, patient care, surgical procedures, nursing, and health sciences."),
        "science": ("Pure & Applied Science / Research", "🔬", "Focused on scientific research, laboratory experimentation, chemistry, biology, and data analytics."),
        "business": ("Business, Finance & Commerce", "💼", "Focused on business administration, finance, marketing, human resources, and operations."),
        "engineering": ("Engineering & Computer Science", "💻", "Focused on software development, technology systems, data engineering, and technical problem solving.")
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
        feedback.append({"type": "fail", "text": warning_msg})
        action_score = 20.0
        metrics_score = 15.0
        structure_score = 20.0
        length_score = 30.0
        total_score = 20.0
        grade = "F"
    else:
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
        job_matches=jobs_dict_list
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