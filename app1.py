import os
import re
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from fastapi.responses import FileResponse

app = FastAPI(title="RAG AI Resume Analyzer API")

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

# Resume analysis uses lightweight keyword and regex heuristics for reliability.

class MetricResult(BaseModel):
    action_score: float
    metrics_score: float
    structure_score: float
    length_score: float
    total_score: float
    grade: str
    feedback: List[dict]

class JobSuggestion(BaseModel):
    title: str
    match_score: int
    matched_skills: List[str]
    missing_skills: List[str]
    reason: str

class AnalysisResult(BaseModel):
    action_score: float
    metrics_score: float
    structure_score: float
    length_score: float
    total_score: float
    grade: str
    feedback: List[dict]
    detected_skills: List[str]
    company_skills: List[str]
    suggested_jobs: List[JobSuggestion]

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
    "figma": ["figma", "ui ux", "ui/ux"],
    "testing": ["testing", "qa", "selenium"],
    "linux": ["linux", "ubuntu"],
    "cloud": ["cloud", "azure", "gcp", "google cloud"],
}

JOB_CATALOG = [
    {"title": "Python Developer", "skills": ["python", "sql", "fastapi", "django", "flask", "rest api", "git"], "reason": "Strong fit if your resume highlights Python backend development and APIs."},
    {"title": "Backend Developer", "skills": ["java", "sql", "nodejs", "rest api", "docker", "aws", "git"], "reason": "Great match for backend engineering and database-driven applications."},
    {"title": "Full Stack Developer", "skills": ["javascript", "react", "nodejs", "html", "css", "sql", "rest api", "git"], "reason": "A strong option if you have both frontend and backend experience."},
    {"title": "Data Analyst", "skills": ["sql", "excel", "power bi", "tableau", "python", "pandas"], "reason": "Excellent when your resume includes reporting, dashboards, and data analysis."},
    {"title": "Machine Learning Engineer", "skills": ["python", "machine learning", "pandas", "numpy", "sql", "cloud"], "reason": "Best fit for resumes with ML, AI, and Python-based data work."},
    {"title": "DevOps Engineer", "skills": ["aws", "docker", "kubernetes", "linux", "cloud", "git"], "reason": "Suitable when deployment, automation, and cloud platforms are present."},
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


def build_job_recommendations(raw_text: str, company_skills: str = "") -> List[JobSuggestion]:
    resume_skills = set(extract_resume_skills(raw_text))
    company_skill_set = set(parse_company_skills(company_skills))

    suggestions = []
    for job in JOB_CATALOG:
        job_skill_set = set(job["skills"])
        matched_skills = sorted(resume_skills & job_skill_set)
        company_matched = sorted(company_skill_set & job_skill_set)
        missing_skills = sorted(job_skill_set - resume_skills)

        overlap_ratio = len(matched_skills) / max(1, len(job_skill_set))
        company_boost = min(20, len(company_matched) * 10)
        score = min(100, int(round(overlap_ratio * 100 + company_boost)))

        if score >= 45 or matched_skills:
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


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".txt":
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == ".pdf":
        try:
            from pypdf import PdfReader
        except Exception as exc:
            raise HTTPException(status_code=400, detail="PDF parsing requires the 'pypdf' package. Please upload a TXT file or install pypdf.") from exc

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

    raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF or TXT file.")


@app.post("/analyzer", response_model=AnalysisResult)
async def analyze_resume(file: UploadFile = File(...), company_skills: str = Form("")):
    contents = await file.read()
    raw_text = extract_text_from_file(contents, file.filename)

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from the file.")

    # 1. Preprocess the resume text for scoring
    lower_text = raw_text.lower()
    words = re.findall(r"\b\w+\b", raw_text)
    word_count = len(words)

    # 2. Evaluation & Scoring Logic
    feedback = []
    detected_skills = extract_resume_skills(raw_text)
    company_skill_list = parse_company_skills(company_skills)
    suggested_jobs = build_job_recommendations(raw_text, company_skills)

    # Criteria A: Action Verbs
    action_verbs = ["achieved", "developed", "managed", "created", "led", "increased", "reduced",
                    "designed", "implemented", "engineered", "launched", "orchestrated", "automated",
                    "optimized", "built", "assisted", "supported", "coordinated", "handled", "improved"]
    found_verbs = [v for v in action_verbs if v in lower_text]
    found_verbs = list(set(found_verbs))
    action_score = min(100.0, float(len(found_verbs) * 25))

    if len(found_verbs) >= 3:
        feedback.append({"type": "pass", "text": f"Strong semantic action impact detected ({len(found_verbs)} key verbs found)."})
    else:
        feedback.append({"type": "fail", "text": "Low action impact detected. Add stronger verbs (e.g., 'engineered', 'orchestrated')."})

    # Criteria B: Quantifiable Metrics
    numbers = re.findall(r'\b\d+(?:%|\b)', raw_text)
    metrics_score = min(100.0, float(len(numbers) * 35))

    if len(numbers) >= 2:
        feedback.append({"type": "pass", "text": f"Quantifiable achievements detected ({len(numbers)} numerical data points found)."})
    else:
        feedback.append({"type": "fail", "text": "Lacks measurable impact. Incorporate percentages, revenue, or team size metrics."})

    # Criteria C: Structure Completeness
    required_sections = ["education", "experience", "skills"]
    found_sections = [sec for sec in required_sections if sec in lower_text]
    structure_score = (len(found_sections) / len(required_sections)) * 100.0

    if len(found_sections) == len(required_sections):
        feedback.append({"type": "pass", "text": "All standard resume sections detected (Education, Experience, Skills)."})
    else:
        missing = [sec for sec in required_sections if sec not in lower_text]
        feedback.append({"type": "fail", "text": f"Missing critical section headers: {', '.join(missing)}."})

    # Criteria D: Length Check
    if word_count < 120:
        length_score = 60.0
        feedback.append({"type": "fail", "text": f"Resume length is too short ({word_count} words). Aim for 200–500 words."})
    elif word_count > 600:
        length_score = 70.0
        feedback.append({"type": "fail", "text": f"Resume is too verbose ({word_count} words). Condense to 200–500 words."})
    else:
        length_score = 100.0
        feedback.append({"type": "pass", "text": f"Ideal concise length ({word_count} words)."})

    # Calculate Overall Weighted Score
    raw_total = (action_score * 0.30) + (metrics_score * 0.30) + (structure_score * 0.25) + (length_score * 0.15)
    total_score = min(100.0, round(raw_total))

    if total_score >= 85:
        grade = "A"
    elif total_score >= 75:
        grade = "B"
    elif total_score >= 60:
        grade = "C"
    else:
        grade = "D"

    if suggested_jobs:
        feedback.append({"type": "pass", "text": f"Suggested job roles available: {', '.join([job.title for job in suggested_jobs[:3]])}."})
    else:
        feedback.append({"type": "fail", "text": "Add more technical or domain-specific skills so job recommendations can be improved."})

    if company_skill_list:
        feedback.append({"type": "pass", "text": f"Company-skill focus detected: {', '.join(company_skill_list)}."})

    return AnalysisResult(
        action_score=round(action_score),
        metrics_score=round(metrics_score),
        structure_score=round(structure_score),
        length_score=round(length_score),
        total_score=total_score,
        grade=grade,
        feedback=feedback,
        detected_skills=detected_skills,
        company_skills=company_skill_list,
        suggested_jobs=suggested_jobs
    )

if __name__ == "__main__":
    import uvicorn
    import os

    uvicorn.run(
        "app1:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5503")),
        root_path="/",
        reload=False
    )