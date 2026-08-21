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


def validate_resume_document(raw_text: str) -> tuple[bool, str]:
    """Detect if the uploaded text is a valid resume or a non-resume document (like a timetable/schedule)."""
    lower_text = raw_text.lower()
    
    # 1. Timetable / Schedule / Non-resume keywords
    timetable_keywords = [
        "timetable", "time table", "class schedule", "lecture schedule", "period 1", "period 2", "period 3",
        "period 4", "period 5", "room no", "subject code", "course code", "exam schedule", "date sheet",
        "hall ticket", "semester schedule", "lecture time", "daily routine", "invoice", "receipt", "bill",
        "menu card", "syllabus sheet"
    ]
    timetable_hits = [kw for kw in timetable_keywords if kw in lower_text]
    
    # 2. Check resume section headers / anchor keywords
    resume_anchors = [
        "education", "experience", "skills", "projects", "qualification", "employment",
        "work history", "summary", "profile", "contact", "certifications", "curriculum vitae", "resume"
    ]
    anchor_hits = [anchor for anchor in resume_anchors if anchor in lower_text]
    
    if len(timetable_hits) >= 2 or (len(timetable_hits) >= 1 and len(anchor_hits) == 0):
        return False, "⚠️ Non-Resume Document Detected: The uploaded file appears to be a college timetable, class schedule, or non-resume document. Please upload a valid professional resume (Arts, Engineering, Doctor/Medical, Science, Business) for accurate analysis."
    
    if len(anchor_hits) == 0 and len(raw_text.strip().split()) < 40:
        return False, "⚠️ Incomplete Resume Warning: The uploaded text lacks standard resume sections (Education, Skills, Experience). Please upload a complete resume file."
        
    return True, ""


def predict_resume_domain(raw_text: str, detected_skills: List[str]) -> tuple[str, str, str]:
    """Predict resume discipline/domain across 5 major fields."""
    lower_text = raw_text.lower()
    skills_set = set(s.lower() for s in detected_skills)

    domain_scores = {
        "arts": 0,
        "doctor": 0,
        "science": 0,
        "business": 0,
        "engineering": 0
    }

    # 1. Arts, Design & Humanities
    arts_kw = [
        "arts", "b.a", "ba", "m.a", "ma", "fine arts", "bfa", "mfa", "graphic design", "ui/ux", "ui", "ux",
        "figma", "photoshop", "illustrator", "indesign", "canva", "creative writing", "literature", "history",
        "journalism", "copywriting", "content writing", "media", "communication", "film", "acting", "music",
        "theatre", "sociology", "psychology", "philosophy", "animation", "visual arts", "sculpture", "painting",
        "fashion", "interior design", "dribbble", "behance"
    ]
    for kw in arts_kw:
        if kw in lower_text or kw in skills_set:
            domain_scores["arts"] += 2 if kw in ["b.a", "fine arts", "figma", "copywriting", "graphic design", "ui/ux"] else 1

    # 2. Medical & Healthcare / Doctor
    doctor_kw = [
        "mbbs", "md", "ms", "bams", "bhms", "doctor", "physician", "surgeon", "nurse", "nursing", "hospital",
        "clinic", "clinical", "patient", "surgery", "pharmacology", "pharmacy", "medical", "anatomy",
        "physiology", "pathology", "pediatrics", "health", "healthcare", "bds", "dentist", "diagnosis",
        "treatment", "prescription", "icu", "ward", "medical officer", "bls", "acls"
    ]
    for kw in doctor_kw:
        if kw in lower_text or kw in skills_set:
            domain_scores["doctor"] += 3 if kw in ["mbbs", "md", "doctor", "physician", "surgeon", "bds", "nursing"] else 1

    # 3. Pure & Applied Science / Research
    science_kw = [
        "b.sc", "bsc", "m.sc", "msc", "physics", "chemistry", "biology", "biotechnology", "microbiology",
        "biochemistry", "botany", "zoology", "mathematics", "statistics", "genetics", "laboratory", "lab",
        "research paper", "scientific", "spss", "latex", "experiment", "hypothesis", "publication", "astronomy",
        "geology", "research assistant"
    ]
    for kw in science_kw:
        if kw in lower_text or kw in skills_set:
            domain_scores["science"] += 2 if kw in ["b.sc", "m.sc", "biotechnology", "chemistry", "physics", "laboratory"] else 1

    # 4. Business, Finance & Commerce
    business_kw = [
        "bba", "mba", "b.com", "bcom", "m.com", "finance", "accounting", "chartered accountant", "ca", "cpa",
        "marketing", "human resources", "hr", "sales", "business development", "economics", "banking",
        "commerce", "auditing", "excel", "tally", "power bi", "tableau", "crm", "salesforce", "operations",
        "supply chain", "brand manager", "business analyst"
    ]
    for kw in business_kw:
        if kw in lower_text or kw in skills_set:
            domain_scores["business"] += 2 if kw in ["mba", "b.com", "finance", "marketing", "accounting", "human resources"] else 1

    # 5. Engineering & Technology
    eng_kw = [
        "b.tech", "btech", "m.tech", "mtech", "b.e", "be", "computer science", "software", "developer",
        "python", "java", "c++", "c#", "javascript", "react", "node", "sql", "git", "aws", "docker",
        "machine learning", "data science", "ai", "fastapi", "django", "mechanical", "electrical",
        "civil", "electronics", "cad", "autocad", "matlab", "embedded", "engineering"
    ]
    for kw in eng_kw:
        if kw in lower_text or kw in skills_set:
            domain_scores["engineering"] += 2 if kw in ["b.tech", "computer science", "developer", "python", "software"] else 1

    top_domain = max(domain_scores, key=domain_scores.get)
    if domain_scores[top_domain] == 0:
        top_domain = "engineering" # default fallback

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
    # Arts Jobs
    {"domain": "Arts, Design & Humanities", "title": "UI/UX & Visual Designer", "skills": ["figma", "photoshop", "illustrator", "html", "css"], "reason": "Great match for creative design, prototyping, and visual branding profiles."},
    {"domain": "Arts, Design & Humanities", "title": "Content Strategist & Copywriter", "skills": ["copywriting", "excel", "figma"], "reason": "Strong alignment with creative writing, digital media, and content marketing skills."},
    {"domain": "Arts, Design & Humanities", "title": "Graphic Designer & Media Specialist", "skills": ["photoshop", "illustrator", "figma", "canva"], "reason": "Ideal for visual artists, graphic designers, and brand content creators."},
    
    # Doctor / Medical Jobs
    {"domain": "Medical & Healthcare / Doctor", "title": "Resident Medical Officer", "skills": ["patient care", "diagnostics", "bls", "acls"], "reason": "Excellent match for clinical diagnosis, patient management, and emergency care."},
    {"domain": "Medical & Healthcare / Doctor", "title": "Clinical Research Associate", "skills": ["clinical trial", "research", "medical writing"], "reason": "Strong fit for medical research, pharmaceutical studies, and trial management."},
    {"domain": "Medical & Healthcare / Doctor", "title": "Healthcare Administrator", "skills": ["hospital management", "excel", "health informatics"], "reason": "Perfect for clinical operations, healthcare policy, and facility leadership."},
    
    # Science Jobs
    {"domain": "Pure & Applied Science / Research", "title": "Research Scientist & Lab Analyst", "skills": ["laboratory", "spss", "python", "excel"], "reason": "High alignment with lab experimentation, scientific testing, and research data."},
    {"domain": "Pure & Applied Science / Research", "title": "Data Analyst / Statistician", "skills": ["python", "sql", "excel", "spss", "r"], "reason": "Great fit for statistical analysis, hypothesis testing, and quantitative research."},

    # Business Jobs
    {"domain": "Business, Finance & Commerce", "title": "Financial Analyst", "skills": ["excel", "power bi", "tableau", "sql"], "reason": "Ideal match for corporate finance, financial modeling, and data reporting."},
    {"domain": "Business, Finance & Commerce", "title": "Business Analyst", "skills": ["excel", "sql", "tableau", "power bi"], "reason": "Strong fit for business requirement gathering, reporting, and workflow optimization."},
    {"domain": "Business, Finance & Commerce", "title": "Digital Marketing Specialist", "skills": ["copywriting", "excel", "power bi"], "reason": "Great match for performance marketing, campaign management, and customer analytics."},

    # Tech / Engineering Jobs
    {"domain": "Engineering & Computer Science", "title": "Python Developer", "skills": ["python", "sql", "fastapi", "django", "flask", "rest api", "git"], "reason": "Strong fit for Python backend development and API engineering."},
    {"domain": "Engineering & Computer Science", "title": "Full Stack Developer", "skills": ["javascript", "react", "nodejs", "html", "css", "sql", "rest api", "git"], "reason": "A strong option for fullstack web prototyping and application development."},
    {"domain": "Engineering & Computer Science", "title": "DevOps & Cloud Engineer", "skills": ["aws", "docker", "kubernetes", "linux", "cloud", "git"], "reason": "Suitable when deployment, containerization, and cloud platforms are present."}
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
        domain_boost = 30 if is_same_domain else 0
        
        score = min(100, int(round(overlap_ratio * 50 + domain_boost + company_boost)))

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
        # Invalid resume / timetable state
        hackathon_prob = 15.0
        intern_prob = 20.0
        hackathon_status = "⚠️ Document Invalid (Timetable / Schedule Detected)"
        intern_status = "⚠️ Please Upload a Valid Professional Resume"
        
        roadmap.append(StudyTopic(
            category="Resume Validation Required",
            topic="Upload Complete Professional Resume",
            recommendation="Your current document was recognized as a timetable or schedule. Upload a full resume containing Education, Experience, and Skills sections to view tailored recommendations.",
            priority="HIGH",
            impact="Unlocks Accurate Selection Scores & Career Roadmap"
        ))
        return hackathon_prob, intern_prob, hackathon_status, intern_status, roadmap, ["Valid Resume File"]

    # Calculate domain-tailored probabilities & study roadmaps
    if domain_name == "Arts, Design & Humanities":
        hackathon_prob = min(98.0, max(40.0, 50.0 + (len(skills_set & {"figma", "photoshop", "illustrator", "html", "css", "copywriting"}) * 8.0)))
        intern_prob = min(96.0, max(35.0, (total_score * 0.50) + (structure_score * 0.35)))
        hackathon_status = "🎨 Top Design & Case Competition Contender" if hackathon_prob >= 75 else "🎨 Creative Portfolio Contender"
        intern_status = "🌟 Strong Design / Content Internship Candidate" if intern_prob >= 75 else "📈 Competitive Creative Candidate"

        if "figma" not in skills_set:
            skill_gaps.append("Figma & UI/UX Prototyping")
            roadmap.append(StudyTopic(
                category="UI/UX & Visual Design",
                topic="Figma Design Systems & Interactive Wireframing",
                recommendation="Master Figma components, auto-layout, and interactive prototypes to create modern app layouts.",
                priority="HIGH",
                impact="+25% Design Portfolio Pass Rate"
            ))
        if not (skills_set & {"photoshop", "illustrator"}):
            skill_gaps.append("Adobe Creative Suite (Photoshop/Illustrator)")
            roadmap.append(StudyTopic(
                category="Digital Visual Arts",
                topic="Adobe Illustrator & Graphic Branding",
                recommendation="Learn vector logo design, branding systems, and digital asset production for creative campaigns.",
                priority="HIGH",
                impact="+20% Graphic Design Selection Odds"
            ))
        if "copywriting" not in skills_set:
            skill_gaps.append("Content Strategy & SEO Copywriting")
            roadmap.append(StudyTopic(
                category="Content Strategy",
                topic="SEO Copywriting & Digital Brand Storytelling",
                recommendation="Practice writing high-converting headlines, content calendars, and brand stories for online campaigns.",
                priority="MEDIUM",
                impact="+18% Content Strategy Match"
            ))
        roadmap.append(StudyTopic(
            category="Creative Portfolio Showcase",
            topic="Online Design Portfolio (Behance / Dribbble / Medium)",
            recommendation="Publish 3 complete case studies demonstrating your creative process from initial wireframe to final polish.",
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
        roadmap.append(StudyTopic(
            category="Medical Research & Ethics",
            topic="Clinical Research Methodology & Evidence-Based Practice",
            recommendation="Review clinical trial guidelines, patient consent ethics, and scientific medical journal reporting.",
            priority="MEDIUM",
            impact="+20% Medical Fellowship Odds"
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
        roadmap.append(StudyTopic(
            category="Academic Publishing",
            topic="Scientific Manuscript Writing & LaTeX Documentation",
            recommendation="Learn LaTeX formatting for peer-reviewed journal submissions and conference presentations.",
            priority="MEDIUM",
            impact="+20% Scientific Paper Acceptance Rate"
        ))

    elif domain_name == "Business, Finance & Commerce":
        hackathon_prob = min(98.0, max(40.0, 45.0 + (len(skills_set & {"excel", "power bi", "tableau", "sql"}) * 10.0)))
        intern_prob = min(96.0, max(40.0, (total_score * 0.50) + (metrics_score * 0.35)))
        hackathon_status = "💼 Business Case Competition Contender"
        intern_status = "🌟 Strong Business & Finance Internship Candidate" if intern_prob >= 75 else "📈 Competitive Business Associate"

        if not (skills_set & {"power bi", "tableau"}):
            skill_gaps.append("Business Intelligence (Power BI / Tableau)")
            roadmap.append(StudyTopic(
                category="Business Intelligence",
                topic="Interactive Dashboarding with Power BI or Tableau",
                recommendation="Build executive KPI dashboards connecting sales, financial, or operational data sources.",
                priority="HIGH",
                impact="+25% Analytics Role Selection Odds"
            ))
        roadmap.append(StudyTopic(
            category="Financial Modeling",
            topic="Advanced Financial Modeling & Excel Analysis",
            recommendation="Master VLOOKUP, INDEX/MATCH, Pivot Tables, and DCF valuation models for corporate analysis.",
            priority="HIGH",
            impact="+30% Corporate Finance Interview Rate"
        ))
        roadmap.append(StudyTopic(
            category="Agile Project Management",
            topic="Scrum Framework & Agile Project Tracking",
            recommendation="Learn sprint planning, backlog grooming, and team workflow management in Jira or Asana.",
            priority="MEDIUM",
            impact="+18% Operations & Management Match"
        ))

    else:
        # Engineering & Computer Science
        hackathon_prob = min(98.0, max(35.0, 45.0 + (len(skills_set & {"git", "python", "javascript", "react", "fastapi", "aws"}) * 7.0)))
        intern_prob = min(96.0, max(30.0, (total_score * 0.45) + (len(skills_set & {"python", "java", "sql", "git", "rest api"}) * 5.0)))
        hackathon_status = "🔥 Top Tier Hackathon Participant" if hackathon_prob >= 80 else "⚡ Good Prototyping Contender"
        intern_status = "🌟 Strong Software Internship Candidate" if intern_prob >= 78 else "📈 Competitive Technical Fit"

        if "git" not in skills_set:
            skill_gaps.append("Git & GitHub")
            roadmap.append(StudyTopic(
                category="Version Control",
                topic="Git Branching & GitHub Collaboration",
                recommendation="Learn Git commands (clone, commit, push, branch, pull request) and host 2+ repositories on GitHub.",
                priority="HIGH",
                impact="+15% Hackathon & Technical Odds"
            ))
        if not (skills_set & {"fastapi", "nodejs", "django", "flask", "rest api"}):
            skill_gaps.append("REST API & Backend Development")
            roadmap.append(StudyTopic(
                category="Backend Engineering",
                topic="REST API Development (FastAPI or Node.js)",
                recommendation="Build JSON REST APIs, handle HTTP methods (GET, POST, PUT, DELETE), and connect to SQL databases.",
                priority="HIGH",
                impact="+20% Backend Role Match"
            ))
        roadmap.append(StudyTopic(
            category="Computer Science Fundamentals",
            topic="Data Structures, Algorithms & LeetCode",
            recommendation="Solve 3-5 coding problems weekly on Arrays, HashMaps, Strings, Trees, and Time Complexity.",
            priority="HIGH",
            impact="Essential for Technical Internship Interviews"
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
        raw_text = "Experienced candidate proficient in professional resume sections, qualifications, projects, and skills."

    # 1. Document Resume Validation (Non-resume / Timetable check)
    is_valid_resume, warning_msg = validate_resume_document(raw_text)

    # 2. Extract detected skills & Predict Domain
    detected_skills = extract_resume_skills(raw_text)
    domain_name, domain_icon, domain_desc = predict_resume_domain(raw_text, detected_skills)

    # 3. Preprocess for scoring
    lower_text = raw_text.lower()
    words = re.findall(r"\b\w+\b", raw_text)
    word_count = len(words)

    feedback = []
    company_skill_list = parse_company_skills(company_skills)

    if not is_valid_resume:
        feedback.append({"type": "fail", "text": warning_msg})
        action_score = 30.0
        metrics_score = 20.0
        structure_score = 30.0
        length_score = 40.0
        total_score = 28.0
        grade = "F"
    else:
        # Action Verbs
        action_verbs = ["achieved", "developed", "managed", "created", "led", "increased", "reduced",
                        "designed", "implemented", "engineered", "launched", "orchestrated", "automated",
                        "optimized", "built", "assisted", "supported", "coordinated", "handled", "improved"]
        found_verbs = list(set([v for v in action_verbs if v in lower_text]))
        action_score = min(100.0, float(len(found_verbs) * 25))

        if len(found_verbs) >= 2:
            feedback.append({"type": "pass", "text": f"Action impact detected ({len(found_verbs)} key verbs found)."})
        else:
            feedback.append({"type": "fail", "text": "Low action impact detected. Add stronger accomplishment verbs."})

        # Quantifiable Metrics
        numbers = re.findall(r'\b\d+(?:%|\b)', raw_text)
        metrics_score = min(100.0, float(len(numbers) * 35))

        if len(numbers) >= 2:
            feedback.append({"type": "pass", "text": f"Quantifiable achievements detected ({len(numbers)} numerical data points)."})
        else:
            feedback.append({"type": "fail", "text": "Lacks measurable impact. Incorporate percentages, revenue, or key metrics."})

        # Structure
        required_sections = ["education", "experience", "skills"]
        found_sections = [sec for sec in required_sections if sec in lower_text]
        structure_score = (len(found_sections) / len(required_sections)) * 100.0

        if len(found_sections) == len(required_sections):
            feedback.append({"type": "pass", "text": "Standard resume sections detected (Education, Experience, Skills)."})
        else:
            missing = [sec for sec in required_sections if sec not in lower_text]
            feedback.append({"type": "fail", "text": f"Missing recommended section headers: {', '.join(missing)}."})

        # Length
        if word_count < 100:
            length_score = 60.0
            feedback.append({"type": "fail", "text": f"Resume text is short ({word_count} words). Aim for 200–500 words."})
        elif word_count > 600:
            length_score = 75.0
            feedback.append({"type": "fail", "text": f"Resume is verbose ({word_count} words). Condense key bullet points."})
        else:
            length_score = 100.0
            feedback.append({"type": "pass", "text": f"Ideal concise length ({word_count} words)."})

        raw_total = (action_score * 0.30) + (metrics_score * 0.30) + (structure_score * 0.25) + (length_score * 0.15)
        total_score = min(100.0, round(raw_total))

        grade = "A" if total_score >= 85 else ("B" if total_score >= 75 else ("C" if total_score >= 60 else "D"))

    # 4. Job Suggestions tailored to Domain
    suggested_jobs = build_job_recommendations(raw_text, domain_name, company_skills)

    # 5. Probabilities & Domain-Specific Roadmap
    hack_prob, int_prob, hack_status, int_status, roadmap, skill_gaps = calculate_probabilities_and_roadmap(
        raw_text, detected_skills, domain_name, total_score, action_score, metrics_score, structure_score, is_valid_resume
    )

    if is_valid_resume:
        feedback.append({"type": "pass", "text": f"Domain predicted as: {domain_icon} {domain_name}."})

    return AnalysisResult(
        is_valid_resume=is_valid_resume,
        warning_message=warning_msg if not is_valid_resume else None,
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
        skill_gaps=skill_gaps
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
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5503")),
        root_path="/",
        reload=False
    )