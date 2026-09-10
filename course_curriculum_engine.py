import os
import csv
import re
from typing import Dict, List, Optional, Tuple, Any

# Path to courses dataset
COURSES_CSV_PATH = os.path.join(os.path.dirname(__file__), "courses.csv")

# Rich synonym and keyword expansions for common curriculum subjects to ensure high-accuracy semantic matching
SUBJECT_SYNONYMS: Dict[str, List[str]] = {
    "data structures & algorithms": ["dsa", "data structure", "data structures", "algorithms", "algorithm", "trees", "graphs", "dynamic programming", "leetcode", "time complexity"],
    "database management systems": ["dbms", "database", "databases", "sql", "relational database", "rdbms", "postgresql", "mysql", "mongodb", "nosql", "query optimization", "sqlite"],
    "operating systems": ["operating system", "operating systems", "os", "linux", "unix", "kernel", "multithreading", "processes", "memory management", "concurrency", "bash"],
    "computer networks": ["computer network", "computer networks", "networking", "tcp/ip", "udp", "http", "https", "dns", "osi model", "routing", "protocols", "socket programming", "vpn"],
    "web development": ["web development", "web dev", "frontend", "backend", "full stack", "fullstack", "html", "css", "javascript", "typescript", "react", "nodejs", "rest api", "vue", "angular"],
    "software engineering": ["software engineering", "sdlc", "agile", "scrum", "design patterns", "ci/cd", "system design", "code refactoring", "software architecture", "unit testing"],
    "object-oriented programming": ["object-oriented", "object oriented", "oop", "oops", "classes", "inheritance", "polymorphism", "encapsulation", "abstraction"],
    "python programming": ["python", "python3", "pandas", "numpy", "flask", "django", "fastapi", "pytest"],
    "java programming": ["java", "jvm", "spring", "spring boot", "hibernate", "maven", "gradle"],
    "c++ programming": ["c++", "cpp", "stl", "pointers", "templates"],
    "c programming": ["c programming", "c language", "pointers", "memory allocation", "gcc"],
    "machine learning": ["machine learning", "ml", "supervised learning", "unsupervised learning", "scikit-learn", "tensorflow", "pytorch", "neural network", "regression", "classification"],
    "artificial intelligence": ["artificial intelligence", "ai", "genai", "llm", "deep learning", "nlp", "computer vision", "prompt engineering", "transformers"],
    "cloud computing": ["cloud", "aws", "amazon web services", "azure", "gcp", "google cloud", "docker", "kubernetes", "serverless", "lambda", "ec2", "s3"],
    "cyber security": ["cyber security", "cybersecurity", "infosec", "penetration testing", "vulnerability assessment", "cryptography", "firewalls", "owasp", "network security"],
    "data science": ["data science", "data analytics", "data visualization", "pandas", "numpy", "matplotlib", "seaborn", "jupyter", "eda", "statistical analysis"],
    "compiler design": ["compiler", "compiler design", "parsing", "lexical analysis", "ast", "syntax analysis", "code generation"],
    "discrete mathematics": ["discrete math", "discrete mathematics", "graph theory", "set theory", "combinatorics", "boolean algebra"],
    "cad/cam": ["cad", "cam", "autocad", "solidworks", "catia", "3d modeling", "computer aided design"],
    "engineering mechanics": ["engineering mechanics", "statics", "dynamics", "kinematics", "stress analysis"],
    "thermodynamics": ["thermodynamics", "heat transfer", "entropy", "enthalpy", "thermal", "carnot"],
    "fluid mechanics": ["fluid mechanics", "fluid dynamics", "bernoulli", "viscosity", "hydraulics", "cfd"],
    "manufacturing processes": ["manufacturing", "machining", "casting", "welding", "cnc", "fabrication"],
    "strength of materials": ["strength of materials", "som", "tensile strength", "beam deflection", "shear stress", "elasticity"],
    "financial accounting": ["accounting", "financial statements", "balance sheet", "p&l", "general ledger", "reconciliation"],
    "business analytics": ["business analytics", "business intelligence", "power bi", "tableau", "excel modeling", "kpis"],
    "digital marketing": ["digital marketing", "seo", "sem", "social media marketing", "google ads", "content strategy"],
    "human resource management": ["hrm", "human resources", "talent acquisition", "recruitment", "payroll", "employee relations"],
    "clinical diagnostics": ["clinical", "diagnostic", "patient care", "triage", "pathology", "vital signs"],
    "pharmacology": ["pharmacology", "dosage", "prescription", "drugs", "medicinal", "pharmacokinetics"],
    "deep learning": ["deep learning", "dl", "neural network", "neural networks", "cnn", "rnn", "lstm", "transformer", "transformers", "pytorch", "tensorflow"],
    "generative ai": ["generative ai", "genai", "gen-ai", "large language model", "llm", "rag", "retrieval augmented", "langchain", "prompt engineering", "diffusion"],
    "natural language processing": ["nlp", "natural language processing", "text processing", "tokenization", "bert", "gpt", "sentiment analysis", "spacy", "huggingface"],
    "mlops": ["mlops", "model deployment", "model serving", "mlflow", "kubeflow", "ci/cd", "pipeline", "monitoring"],
    "retrieval-augmented generation (rag)": ["rag", "retrieval augmented", "vector database", "vector search", "faiss", "pinecone", "chromadb", "embeddings"],
    "linear algebra": ["linear algebra", "matrices", "matrix", "vectors", "eigenvalues", "pca"],
    "probability & statistics": ["probability", "statistics", "statistical", "bayesian", "hypothesis testing", "distributions"],
    "computer vision": ["computer vision", "cv", "opencv", "yolo", "object detection", "image classification"],
    "analog electronics": ["analog electronics", "analog circuits", "op-amp", "operational amplifier", "bjt", "mosfet", "diodes"],
    "digital electronics": ["digital electronics", "logic gates", "flip-flops", "boolean logic", "combinational circuits", "sequential circuits"],
    "embedded systems": ["embedded systems", "embedded", "microcontroller", "arduino", "raspberry pi", "arm", "rtos", "firmware"],
    "vlsi design": ["vlsi", "verilog", "vhdl", "asic", "fpga", "cadence", "cmos", "circuit layout"],
    "signals & systems": ["signals and systems", "fourier transform", "laplace transform", "z-transform", "dsp", "digital signal processing"],
    "control systems": ["control systems", "bode plot", "pid controller", "nyquist", "state space", "feedback control"],
    "communication systems": ["communication systems", "modulation", "am", "fm", "wireless", "rf", "antenna", "signal transmission"],
    "microprocessors & microcontrollers": ["microprocessor", "microcontrollers", "8085", "8086", "arm cortex", "pic", "assembly language"]
}


class CourseCurriculumEngine:
    def __init__(self, csv_path: str = COURSES_CSV_PATH):
        self.csv_path = csv_path
        self.courses: List[Dict[str, Any]] = []
        self.courses_by_name: Dict[str, Dict[str, Any]] = {}
        self.categories: List[str] = []
        self.levels: List[str] = ["UG", "PG", "Diploma"]
        self.load_dataset()

    def load_dataset(self):
        """Loads and indexes all courses, levels, categories, and major subjects from CSV."""
        if not os.path.exists(self.csv_path):
            alt_path = os.path.join(os.path.dirname(__file__), ".agents", "skills", "ui-ux-pro-max", "data", "courses.csv")
            if os.path.exists(alt_path):
                self.csv_path = alt_path
            else:
                return

        courses_map: Dict[Tuple[str, str, str], List[str]] = {}
        with open(self.csv_path, mode="r", encoding="utf-8-sig", errors="ignore") as f:
            reader = csv.DictReader(f)
            for raw_row in reader:
                row = {k.strip().replace('\ufeff', ''): v for k, v in raw_row.items() if k}
                course_name = (row.get("Course Name") or "").strip()
                course_level = (row.get("Course Level") or "").strip().upper()
                category = (row.get("Category") or "").strip()
                subject = (row.get("Major Subject") or "").strip()

                if not course_name or not subject:
                    continue

                key = (course_name, course_level, category)
                if key not in courses_map:
                    courses_map[key] = []
                if subject not in courses_map[key]:
                    courses_map[key].append(subject)

        self.courses = []
        self.courses_by_name = {}
        categories_set = set()

        for (name, level, cat), subjects in courses_map.items():
            record = {
                "course_name": name,
                "course_level": level,
                "category": cat,
                "major_subjects": subjects,
                "total_subjects": len(subjects)
            }
            self.courses.append(record)
            self.courses_by_name[name.lower()] = record
            categories_set.add(cat)

        self.categories = sorted(list(categories_set))
        print(f"[CourseCurriculumEngine] Successfully indexed {len(self.courses)} distinct courses across {len(self.categories)} categories.")

    def search_courses(self, query: str = "", level: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches and filters courses by keyword, level, or category."""
        q = query.strip().lower()
        results = []
        for c in self.courses:
            if level and c["course_level"].lower() != level.strip().lower():
                continue
            if category and c["category"].lower() != category.strip().lower():
                continue
            if q:
                in_name = q in c["course_name"].lower()
                in_cat = q in c["category"].lower()
                in_subjects = any(q in sub.lower() for sub in c["major_subjects"])
                if not (in_name or in_cat or in_subjects):
                    continue
            results.append({
                "course_name": c["course_name"],
                "course_level": c["course_level"],
                "category": c["category"],
                "total_subjects": c["total_subjects"],
                "sample_subjects": c["major_subjects"][:5]
            })
        return results

    def get_course_details(self, course_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves complete syllabus record for a course."""
        c = self.courses_by_name.get(course_name.strip().lower())
        if not c:
            q = course_name.strip().lower()
            for name, rec in self.courses_by_name.items():
                if q in name or name in q:
                    return rec
            return None
        return c

    def match_resume_to_curriculum(self, raw_text: str, detected_skills: List[str] = None) -> Dict[str, Any]:
        """
        State-of-the-art semantic curriculum matcher.
        Scores candidate text against all 220 official courses in courses.csv considering:
        1. Exact Degree/Course Name mentions in education sections (e.g. 'Computer Science', 'BCA', 'Aeronautical')
        2. Course Level indicators (B.Tech/BE/BSc -> UG, M.Tech/MSc/MBA -> PG, Diploma/Polytechnic -> Diploma)
        3. Major Subject keyword coverage in candidate projects, skills, and experience
        """
        if not self.courses:
            return self._empty_match()

        text_lower = raw_text.lower()
        skills_set = set(s.lower() for s in (detected_skills or []))

        # 1. Accurately detect candidate level using word boundaries
        detected_level = None
        has_ug = bool(re.search(r"\b(b\.?tech|btech|b\.?e\.?|b\.?sc|bsc|bba|bca|b\.?com|bcom|bachelor|undergraduate|ug)\b", text_lower))
        has_pg = bool(re.search(r"\b(m\.?tech|mtech|m\.?e\.?|m\.?sc|msc|mba|mca|m\.?com|mcom|masters|post\s*graduate|pg)\b", text_lower))
        has_diploma = bool(re.search(r"\b(diploma|polytechnic)\b", text_lower))

        if has_pg and not has_ug:
            detected_level = "PG"
        elif has_ug:
            detected_level = "UG"
        elif has_diploma:
            detected_level = "Diploma"
        else:
            detected_level = "UG"

        candidate_scores: List[Tuple[Dict[str, Any], float, int]] = []

        for c in self.courses:
            score = 0.0
            course_name_lower = c["course_name"].lower()
            course_level = c["course_level"]

            # A. Title Match Bonus with word boundary check
            escaped_name = re.escape(course_name_lower)
            if re.search(r"\b" + escaped_name + r"\b", text_lower):
                score += 50.0
                # Extra boost if mentioned along with degree keywords (e.g. 'b.tech in data science')
                if re.search(r"(degree|b\.?tech|m\.?tech|b\.?e|m\.?e|bachelor|master|diploma).*?" + escaped_name, text_lower):
                    score += 25.0
            else:
                stop_words = ["and", "engineering", "technology", "studies", "science", "arts", "general"]
                tokens = [t for t in re.split(r"[\s&/,()\-]+", course_name_lower) if len(t) > 2 and t not in stop_words]
                if tokens:
                    token_hits = sum(1 for t in tokens if re.search(r"\b" + re.escape(t) + r"\b", text_lower))
                    score += (token_hits / len(tokens)) * 25.0

            # B. Level Alignment
            if course_level == detected_level:
                score += 15.0
            elif detected_level == "UG" and course_level == "Diploma":
                score -= 10.0
            elif detected_level == "Diploma" and course_level == "UG":
                score -= 5.0

            # C. Major Subject Alignment
            subject_hits = 0
            for subject in c["major_subjects"]:
                sub_lower = subject.lower()
                is_hit = False
                if sub_lower in text_lower or re.search(r"\b" + re.escape(sub_lower) + r"\b", text_lower):
                    is_hit = True
                else:
                    synonyms = SUBJECT_SYNONYMS.get(sub_lower, [])
                    if any(syn in text_lower or syn in skills_set for syn in synonyms):
                        is_hit = True

                if is_hit:
                    subject_hits += 1

            subject_ratio = subject_hits / max(1, len(c["major_subjects"]))
            score += subject_ratio * 45.0

            candidate_scores.append((c, score, subject_hits))

        # Sort descending by score
        candidate_scores.sort(key=lambda x: x[1], reverse=True)

        best_course, best_score, best_hits = candidate_scores[0]
        match_confidence = min(98, max(52, round(best_score * 0.95)))

        audit_result = self.audit_course_subjects(best_course, raw_text, detected_skills)

        alternative_courses = []
        for alt_c, alt_s, alt_h in candidate_scores[1:4]:
            if alt_c["course_name"] != best_course["course_name"]:
                alternative_courses.append({
                    "course_name": alt_c["course_name"],
                    "course_level": alt_c["course_level"],
                    "category": alt_c["category"],
                    "match_score": min(95, max(45, round(alt_s * 0.9))),
                    "matching_subjects_count": alt_h,
                    "total_subjects": alt_c["total_subjects"]
                })

        pathways = self.get_higher_education_pathway(best_course)

        return {
            "matched_course": {
                "course_name": best_course["course_name"],
                "course_level": best_course["course_level"],
                "category": best_course["category"],
                "match_confidence": match_confidence,
                "total_curriculum_subjects": best_course["total_subjects"]
            },
            "detected_level": detected_level or best_course["course_level"],
            "curriculum_score": audit_result["curriculum_coverage_score"],
            "mastered_count": len(audit_result["mastered_subjects"]),
            "partial_count": len(audit_result["partial_subjects"]),
            "gap_count": len(audit_result["gap_subjects"]),
            "mastered_subjects": audit_result["mastered_subjects"],
            "partial_subjects": audit_result["partial_subjects"],
            "gap_subjects": audit_result["gap_subjects"],
            "all_subject_evaluations": audit_result["all_evaluations"],
            "alternative_courses": alternative_courses,
            "higher_education_pathway": pathways,
            "curriculum_summary": f"Curriculum analysis matched profile to '{best_course['course_name']}' ({best_course['course_level']} - {best_course['category']}) with {audit_result['curriculum_coverage_score']}% syllabus evidence ({len(audit_result['mastered_subjects'])}/{best_course['total_subjects']} core subjects verified)."
        }

    def audit_course_subjects(self, course: Dict[str, Any], raw_text: str, detected_skills: List[str] = None) -> Dict[str, Any]:
        """
        Audits candidate resume against every official Major Subject in the target course.
        Categorizes each subject as MASTERED, PARTIAL, or GAP, with quote snippets.
        """
        text_lower = raw_text.lower()
        skills_set = set(s.lower() for s in (detected_skills or []))
        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

        mastered = []
        partial = []
        gaps = []
        all_evals = []

        for subject in course["major_subjects"]:
            sub_lower = subject.lower()
            synonyms = SUBJECT_SYNONYMS.get(sub_lower, [])

            found_quote = ""
            is_mastered = False
            is_partial = False

            # Check 1: Direct exact subject mention in text
            for line in lines:
                line_lower = line.lower()
                if sub_lower in line_lower:
                    is_mastered = True
                    found_quote = line[:120] + ("..." if len(line) > 120 else "")
                    break

            # Check 2: Check synonyms / technologies
            if not is_mastered and synonyms:
                matching_syns = []
                for syn in synonyms:
                    if syn in skills_set or syn in text_lower:
                        matching_syns.append(syn)
                        if not found_quote:
                            for line in lines:
                                if syn in line.lower():
                                    found_quote = line[:120] + ("..." if len(line) > 120 else "")
                                    break

                if len(matching_syns) >= 2:
                    is_mastered = True
                elif len(matching_syns) == 1:
                    is_partial = True

            # Check 3: Check single word roots if technical domain
            if not is_mastered and not is_partial:
                tokens = [t for t in re.split(r"[\s&/,()\-]+", sub_lower) if len(t) > 3 and t not in ["engineering", "science", "system", "systems", "technologies", "technology", "studies", "principles", "methods"]]
                matched_tokens = [t for t in tokens if re.search(r"\b" + re.escape(t) + r"\b", text_lower)]
                if len(matched_tokens) >= 2 or (len(tokens) == 1 and len(matched_tokens) == 1):
                    is_partial = True
                    if not found_quote:
                        for line in lines:
                            if any(mt in line.lower() for mt in matched_tokens):
                                found_quote = line[:120] + ("..." if len(line) > 120 else "")
                                break

            # Formulate audit item
            if is_mastered:
                item = {
                    "subject": subject,
                    "status": "MASTERED",
                    "status_badge": "🟢 Verified in Resume",
                    "evidence_quote": found_quote or f"Direct evidence of {subject} found in skills/project history.",
                    "study_action": f"Solid core foundation verified. Apply {subject} to advanced scalable portfolio projects."
                }
                mastered.append(item)
            elif is_partial:
                item = {
                    "subject": subject,
                    "status": "PARTIAL",
                    "status_badge": "🟡 Partial Evidence",
                    "evidence_quote": found_quote or f"Related tools/topics detected without dedicated project depth.",
                    "study_action": f"Demonstrate end-to-end practical implementation of {subject} in your resume projects."
                }
                partial.append(item)
            else:
                item = {
                    "subject": subject,
                    "status": "GAP",
                    "status_badge": "🔴 Missing Syllabus Subject",
                    "evidence_quote": "Not mentioned in uploaded resume.",
                    "study_action": f"High ATS Priority: Core course subject '{subject}' is missing. Study fundamentals & highlight in skills."
                }
                gaps.append(item)

            all_evals.append(item)

        total_subjects = max(1, len(course["major_subjects"]))
        coverage_score = round(((len(mastered) * 1.0 + len(partial) * 0.5) / total_subjects) * 100)

        return {
            "curriculum_coverage_score": coverage_score,
            "mastered_subjects": mastered,
            "partial_subjects": partial,
            "gap_subjects": gaps,
            "all_evaluations": all_evals
        }

    def get_higher_education_pathway(self, current_course: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Maps career progression and higher education degrees from courses.csv.
        Diploma -> UG programs
        UG -> PG specializations (M.Tech, MCA, M.E., MBA, MD, M.Des, LLM, etc.)
        """
        curr_level = current_course["course_level"]
        curr_cat = current_course["category"]
        curr_name = current_course["course_name"]

        target_level = "PG" if curr_level in ["UG", "PG"] else "UG"
        pathway_courses = []

        # Category to preferred degree keywords
        preferred_pg = []
        if any(k in curr_cat for k in ["Computer", "Engineering"]):
            preferred_pg = ["M.Tech", "MCA", "M.E.", "M.Sc", "MBA"]
        elif any(k in curr_cat for k in ["Management", "Commerce"]):
            preferred_pg = ["MBA", "M.Com"]
        elif any(k in curr_cat for k in ["Design", "Architecture"]):
            preferred_pg = ["M.Des", "M.Arch", "M.Plan"]
        elif any(k in curr_cat for k in ["Medicine", "Healthcare", "Medical"]):
            preferred_pg = ["MD General Medicine", "M.Sc Nursing", "M.Pharm", "MPH", "MHA"]
        elif "Law" in curr_cat:
            preferred_pg = ["LLM"]
        elif "Education" in curr_cat:
            preferred_pg = ["M.Ed", "M.A."]
        elif "Science" in curr_cat:
            preferred_pg = ["M.Sc", "M.Tech"]
        else:
            preferred_pg = ["M.Tech", "MBA", "M.Sc", "MCA"]

        if curr_level == "Diploma":
            # For Diploma, recommend related UG programs
            for c in self.courses:
                if c["course_level"] == "UG":
                    # Check subject or category match
                    if any(t in c["category"].lower() for t in ["engineering", "computer", "technology", "science"]):
                        pathway_courses.append({
                            "course_name": c["course_name"],
                            "course_level": c["course_level"],
                            "category": c["category"],
                            "highlight_subjects": c["major_subjects"][:3],
                            "rationale": f"Direct progression into Undergraduate (UG) degree from Diploma in {curr_name}."
                        })
                        if len(pathway_courses) >= 4:
                            break
        else:
            # For UG / PG, recommend target PG specializations
            for pg_name in preferred_pg:
                c = self.courses_by_name.get(pg_name.lower())
                if c and c["course_name"] != curr_name:
                    pathway_courses.append({
                        "course_name": c["course_name"],
                        "course_level": c["course_level"],
                        "category": c["category"],
                        "highlight_subjects": c["major_subjects"][:3],
                        "rationale": f"Authoritative postgraduate specialization from syllabus dataset to accelerate career beyond {curr_name}."
                    })

        if not pathway_courses:
            for c in self.courses:
                if c["course_level"] == "PG":
                    pathway_courses.append({
                        "course_name": c["course_name"],
                        "course_level": c["course_level"],
                        "category": c["category"],
                        "highlight_subjects": c["major_subjects"][:3],
                        "rationale": "Recommended postgraduate program from official university curriculum."
                    })
                    if len(pathway_courses) >= 3:
                        break

        return pathway_courses[:4]

    def _empty_match(self) -> Dict[str, Any]:
        return {
            "matched_course": {
                "course_name": "General Higher Education",
                "course_level": "UG",
                "category": "Academic",
                "match_confidence": 60,
                "total_curriculum_subjects": 0
            },
            "detected_level": "UG",
            "curriculum_score": 50,
            "mastered_count": 0,
            "partial_count": 0,
            "gap_count": 0,
            "mastered_subjects": [],
            "partial_subjects": [],
            "gap_subjects": [],
            "all_subject_evaluations": [],
            "alternative_courses": [],
            "higher_education_pathway": [],
            "curriculum_summary": "Course curriculum dataset could not be loaded."
        }


# Singleton instance
curriculum_engine = CourseCurriculumEngine()
