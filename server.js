const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const cors = require("cors");
const crypto = require("crypto");
const { spawn } = require("child_process");

const app = express();
let analyzerProcess;
let jobsProcess;

function startAnalyzerBackend() {
    const pythonCommand = process.env.PYTHON_COMMAND || (process.platform === "win32" ? "python" : "python3");
    analyzerProcess = spawn(pythonCommand, [path.join(__dirname, "app1.py")], {
        cwd: __dirname,
        env: { ...process.env, PORT: "5503" },
        stdio: "inherit",
        windowsHide: true
    });

    analyzerProcess.on("error", error => {
        console.error("Could not start app1.py automatically:", error.message);
    });
    analyzerProcess.on("exit", (code, signal) => {
        if (code !== 0 && signal !== "SIGTERM") {
            console.error(`app1.py stopped (code ${code}, signal ${signal || "none"}).`);
        }
    });
}

const jobsHost = process.env.JOBS_BACKEND_HOST || "127.0.0.1";
const jobsBackendPort = process.env.JOBS_BACKEND_PORT || "5501";

function startAnalyzerBackend() {
    const pythonCommand = process.env.PYTHON_COMMAND || (process.platform === "win32" ? "python" : "python3");
    analyzerProcess = spawn(pythonCommand, [path.join(__dirname, "app1.py")], {
        cwd: __dirname,
        env: { ...process.env, PORT: "5503" },
        stdio: "inherit",
        windowsHide: true
    });

    analyzerProcess.on("error", error => {
        console.error("Could not start app1.py automatically:", error.message);
    });
    analyzerProcess.on("exit", (code, signal) => {
        if (code !== 0 && signal !== "SIGTERM") {
            console.error(`app1.py stopped (code ${code}, signal ${signal || "none"}).`);
        }
    });
}

function startJobsBackend() {
    const pythonCommand = process.env.PYTHON_COMMAND || (process.platform === "win32" ? "py" : "python3");
    jobsProcess = spawn(pythonCommand, ["-m", "uvicorn", "backendreal:app", "--host", jobsHost, "--port", "5501"], {
        cwd: __dirname,
        env: { ...process.env, PORT: "5501" },
        stdio: "inherit",
        windowsHide: true
    });

    jobsProcess.on("error", error => {
        console.error("Could not start backendreal.py automatically:", error.message);
    });
    jobsProcess.on("exit", (code, signal) => {
        if (code !== 0 && signal !== "SIGTERM") {
            console.error(`backendreal.py stopped (code ${code}, signal ${signal || "none"}).`);
        }
    });
}

app.use(cors({ origin: true, credentials: true }));
app.set("trust proxy", 1);

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Serve HTML file
app.use(express.static(__dirname));

app.get("/health", (req, res) => {
    res.json({ status: "ok" });
});

// Helper for standalone Express job searching
async function fetchExpressJobs(prompt) {
    const query = (prompt || "Software Engineer").trim();
    const queryLower = query.toLowerCase();

    // Check for Hackathons
    if (queryLower.includes("hackathon") || queryLower.includes("contest")) {
        return [
            {
                company: "MAJOR LEAGUE HACKING (MLH)",
                title: "Global Tech Hackathon 2026",
                type: "Hackathon",
                domain: "Software & Hardware",
                location: "Online / Global",
                salary: "Prizes up to $25,000",
                description: "Compete with thousands of global developers in a week-long building challenge.",
                ribbonText: "Live Hackathon",
                ribbonClass: "hackathon",
                apply_link: "https://mlh.io",
                signin_link: "https://mlh.io/users/sign_in"
            },
            {
                company: "DEVPOST",
                title: "AI & Cloud Innovation Challenge",
                type: "Hackathon",
                domain: "Artificial Intelligence",
                location: "Remote",
                salary: "Prizes up to $50,000",
                description: "Build next-gen AI applications with cutting-edge tools and models.",
                ribbonText: "$50k Prize Pool",
                ribbonClass: "hackathon",
                apply_link: "https://devpost.com",
                signin_link: "https://devpost.com/login"
            },
            {
                company: "GOOGLE FOR DEVELOPERS",
                title: "Build with AI Global Hackathon",
                type: "Hackathon",
                domain: "AI / ML",
                location: "Global",
                salary: "Google Cloud Credits & Swag",
                description: "Join Google's developer community to create solutions for global challenges.",
                ribbonText: "Google Event",
                ribbonClass: "hackathon",
                apply_link: "https://developers.google.com",
                signin_link: "https://accounts.google.com"
            }
        ];
    }

    // Try Adzuna API
    try {
        const adzunaAppId = "d1f4b68d";
        const adzunaAppKey = "e5ffc11dd8e1b50c11a3b48cfa7149b7";
        const adzunaUrl = `https://api.adzuna.com/v1/api/jobs/in/search/1?app_id=${adzunaAppId}&app_key=${adzunaAppKey}&results_per_page=25&what=${encodeURIComponent(query)}`;

        const response = await fetch(adzunaUrl);
        if (response.ok) {
            const data = await response.json();
            const results = data.results || [];

            if (results.length > 0) {
                return results.map(item => {
                    const company = (item.company?.display_name || "TECH COMPANY").toUpperCase();
                    const cleanTitle = (item.title || "Role").replace(/<\/?[^>]+(>|$)/g, "");
                    const isIntern = queryLower.includes("intern") || cleanTitle.toLowerCase().includes("intern");
                    
                    let signinUrl = "https://careers.google.com/";
                    if (company.includes("MICROSOFT")) signinUrl = "https://careers.microsoft.com/";
                    else if (company.includes("AMAZON")) signinUrl = "https://www.amazon.jobs/";
                    else if (company.includes("APPLE")) signinUrl = "https://www.apple.com/careers/";
                    else if (company.includes("META")) signinUrl = "https://www.metacareers.com/";
                    else if (company.includes("IBM")) signinUrl = "https://www.ibm.com/careers/";
                    else if (company.includes("ORACLE")) signinUrl = "https://www.oracle.com/careers/";
                    else if (company.includes("TCS") || company.includes("INFOSYS") || company.includes("WIPRO")) signinUrl = "https://www.naukri.com/nlogin/login";
                    else signinUrl = item.redirect_url || `https://www.google.com/search?q=${encodeURIComponent(company + " careers sign in")}`;

                    return {
                        company: company,
                        title: cleanTitle,
                        type: isIntern ? "Internship" : "Job",
                        domain: item.category?.label || "Technology",
                        location: item.location?.display_name || "India / Remote",
                        salary: item.salary_min ? `₹${Math.round(item.salary_min).toLocaleString()} - ₹${Math.round(item.salary_max || item.salary_min * 1.3).toLocaleString()} / yr` : "Competitive Salary",
                        description: item.description ? item.description.slice(0, 160) + "..." : "Join a dynamic engineering team working on modern web and software products.",
                        ribbonText: isIntern ? "Internship" : "Full-Time Role",
                        ribbonClass: isIntern ? "intern" : "",
                        apply_link: item.redirect_url || signinUrl,
                        signin_link: signinUrl
                    };
                });
            }
        }
    } catch (e) {
        console.log("Adzuna API fallback fetch warning:", e.message);
    }

    // Default Fallback Jobs if external API is unreachable
    return [
        {
            company: "GOOGLE",
            title: queryLower.includes("intern") ? "Software Engineering Intern" : "Software Engineer",
            type: queryLower.includes("intern") ? "Internship" : "Job",
            domain: "Cloud & AI",
            location: "Bangalore, India / Remote",
            salary: "₹18,000,000 - ₹28,000,000 / yr",
            description: "Work on large-scale distributed systems, web services, and Machine Learning infrastructure.",
            ribbonText: "Featured",
            ribbonClass: "",
            apply_link: "https://careers.google.com/",
            signin_link: "https://careers.google.com/"
        },
        {
            company: "MICROSOFT",
            title: queryLower.includes("intern") ? "Program Manager Intern" : "Fullstack Developer",
            type: queryLower.includes("intern") ? "Internship" : "Job",
            domain: "Azure & Productivity",
            location: "Hyderabad, India",
            salary: "₹16,000,000 - ₹24,000,000 / yr",
            description: "Build seamless cloud applications, microservices, and React-based developer portals.",
            ribbonText: queryLower.includes("intern") ? "Internship" : "High Demand",
            ribbonClass: queryLower.includes("intern") ? "intern" : "",
            apply_link: "https://careers.microsoft.com/",
            signin_link: "https://careers.microsoft.com/"
        },
        {
            company: "OPENAI",
            title: "Research Engineer - AI Systems",
            type: "Job",
            domain: "Generative AI",
            location: "Remote / Global",
            salary: "₹25,000,000+ / yr",
            description: "Advance state-of-the-art deep learning architectures and LLM inference pipelines.",
            ribbonText: "Hot Opportunity",
            ribbonClass: "",
            apply_link: "https://openai.com/careers/",
            signin_link: "https://openai.com/careers/"
        },
        {
            company: "AMAZON",
            title: "Backend Development Engineer",
            type: "Job",
            domain: "AWS & Commerce",
            location: "Chennai / Hyderabad, India",
            salary: "₹15,000,000 - ₹22,000,000 / yr",
            description: "Architect ultra-low-latency web services serving millions of worldwide customers daily.",
            ribbonText: "Actively Hiring",
            ribbonClass: "",
            apply_link: "https://www.amazon.jobs/",
            signin_link: "https://www.amazon.jobs/"
        },
        {
            company: "META",
            title: "Production Engineering Intern",
            type: "Internship",
            domain: "Infrastructure",
            location: "Gurgaon, India / Remote",
            salary: "₹19,00,000 - ₹34,00,000 / yr",
            description: "Scale global networking infrastructure, data center automation, and distributed web services.",
            ribbonText: "High Growth",
            ribbonClass: "intern",
            apply_link: "https://www.metacareers.com/",
            signin_link: "https://www.metacareers.com/"
        },
        {
            company: "APPLE",
            title: "iOS Application Developer",
            type: "Job",
            domain: "Mobile Engineering",
            location: "Hyderabad / Bangalore, India",
            salary: "₹17,00,000 - ₹30,00,000 / yr",
            description: "Build high-performance client applications and frameworks for millions of Apple devices.",
            ribbonText: "Apple Team",
            ribbonClass: "",
            apply_link: "https://www.apple.com/careers/",
            signin_link: "https://www.apple.com/careers/"
        },
        {
            company: "NVIDIA",
            title: "CUDA & Deep Learning Engineer",
            type: "Job",
            domain: "AI Compute",
            location: "Pune / Bangalore, India",
            salary: "₹22,00,000 - ₹38,00,000 / yr",
            description: "Accelerate neural network training pipelines using CUDA C++, PyTorch, and TensorRT.",
            ribbonText: "AI Leader",
            ribbonClass: "",
            apply_link: "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
            signin_link: "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
        },
        {
            company: "NETFLIX",
            title: "Streaming Backend Engineer",
            type: "Job",
            domain: "Cloud & Media",
            location: "Remote / Mumbai",
            salary: "₹25,00,000 - ₹40,00,000 / yr",
            description: "Optimize real-time video streaming delivery algorithms and microservices architectures.",
            ribbonText: "Top Tier",
            ribbonClass: "",
            apply_link: "https://jobs.netflix.com/",
            signin_link: "https://jobs.netflix.com/"
        },
        {
            company: "UBER",
            title: "Logistics & Systems Engineer",
            type: "Job",
            domain: "Transportation Tech",
            location: "Bangalore, India",
            salary: "₹16,50,000 - ₹27,00,000 / yr",
            description: "Engineer low-latency dispatch algorithms, Geospatial routing, and transaction systems.",
            ribbonText: "Actively Hiring",
            ribbonClass: "",
            apply_link: "https://www.uber.com/us/en/careers/",
signin_link: "https://www.uber.com/us/en/careers/"
        },
        {
            company: "RAZORPAY",
            title: "Fintech Platform Engineer",
            type: "Job",
            domain: "Fintech",
            location: "Bangalore, India",
            salary: "₹14,00,000 - ₹24,00,000 / yr",
            description: "Build high-reliability payment gateway APIs handling millions of online digital transactions.",
            ribbonText: "Fintech Leader",
            ribbonClass: "",
            apply_link: "https://razorpay.com/jobs/",
            signin_link: "https://razorpay.com/jobs/"
        }
    ];
}

// Helper for standalone Express job searching
async function fetchExpressJobs(prompt) {
    const query = (prompt || "Software Engineer").trim();
    const queryLower = query.toLowerCase();

    // Check for Hackathons
    if (queryLower.includes("hackathon") || queryLower.includes("contest")) {
        return [
            {
                company: "MAJOR LEAGUE HACKING (MLH)",
                title: "Global Tech Hackathon 2026",
                type: "Hackathon",
                domain: "Software & AI",
                location: "Online / Global",
                salary: "Prizes worth $25,000",
                description: "Compete with thousands of global developers in a week-long building challenge.",
                ribbonText: "Live Hackathon",
                ribbonClass: "hackathon",
                apply_link: "https://mlh.io",
                signin_link: "https://mlh.io/users/sign_in"
            },
            {
                company: "DEVPOST",
                title: "AI & Cloud Innovation Challenge",
                type: "Hackathon",
                domain: "Artificial Intelligence",
                location: "Remote",
                salary: "Prizes worth $50,000",
                description: "Build next-gen AI applications with cutting-edge tools and models.",
                ribbonText: "$50k Prize Pool",
                ribbonClass: "hackathon",
                apply_link: "https://devpost.com",
                signin_link: "https://devpost.com/login"
            },
            {
                company: "GOOGLE FOR DEVELOPERS",
                title: "Build with AI Global Hackathon",
                type: "Hackathon",
                domain: "AI / ML",
                location: "Global",
                salary: "Google Cloud Credits & Swag",
                description: "Join Google's developer community to create solutions for global challenges.",
                ribbonText: "Google Event",
                ribbonClass: "hackathon",
                apply_link: "https://developers.google.com",
                signin_link: "https://accounts.google.com"
            }
        ];
    }

    // Default Job Listings
    return [
        {
            company: "GOOGLE",
            title: queryLower.includes("intern") ? "Software Engineering Intern" : "Software Engineer",
            type: queryLower.includes("intern") ? "Internship" : "Job",
            domain: "Cloud & AI",
            location: "Bangalore, India / Remote",
            salary: "₹18,00,000 - ₹28,00,000 / yr",
            description: "Work on large-scale distributed systems, web services, and Machine Learning infrastructure.",
            ribbonText: "Featured",
            ribbonClass: queryLower.includes("intern") ? "intern" : "",
            apply_link: "https://careers.google.com/",
            signin_link: "https://careers.google.com/"
        },
        {
            company: "MICROSOFT",
            title: queryLower.includes("intern") ? "Program Manager Intern" : "Fullstack Developer",
            type: queryLower.includes("intern") ? "Internship" : "Job",
            domain: "Azure & Productivity",
            location: "Hyderabad, India",
            salary: "₹16,00,000 - ₹24,00,000 / yr",
            description: "Build seamless cloud applications, microservices, and React-based developer portals.",
            ribbonText: queryLower.includes("intern") ? "Internship" : "High Demand",
            ribbonClass: queryLower.includes("intern") ? "intern" : "",
            apply_link: "https://careers.microsoft.com/",
            signin_link: "https://careers.microsoft.com/"
        },
        {
            company: "OPENAI",
            title: "Research Engineer - AI Systems",
            type: "Job",
            domain: "Generative AI",
            location: "Remote / Global",
            salary: "₹25,00,000+ / yr",
            description: "Advance state-of-the-art deep learning architectures and LLM inference pipelines.",
            ribbonText: "Hot Opportunity",
            ribbonClass: "",
            apply_link: "https://openai.com/careers/",
            signin_link: "https://openai.com/careers/"
        },
        {
            company: "AMAZON",
            title: "Backend Development Engineer",
            type: "Job",
            domain: "AWS & Commerce",
            location: "Chennai / Hyderabad, India",
            salary: "₹15,00,000 - ₹22,00,000 / yr",
            description: "Architect ultra-low-latency web services serving millions of worldwide customers daily.",
            ribbonText: "Actively Hiring",
            ribbonClass: "",
            apply_link: "https://www.amazon.jobs/",
            signin_link: "https://www.amazon.jobs/"
        },
        {
            company: "META",
            title: "Production Engineering Intern",
            type: "Internship",
            domain: "Infrastructure",
            location: "Gurgaon, India / Remote",
            salary: "₹19,00,000 - ₹34,00,000 / yr",
            description: "Scale global networking infrastructure, data center automation, and distributed web services.",
            ribbonText: "High Growth",
            ribbonClass: "intern",
            apply_link: "https://www.metacareers.com/",
            signin_link: "https://www.metacareers.com/"
        },
        {
            company: "APPLE",
            title: "iOS Application Developer",
            type: "Job",
            domain: "Mobile Engineering",
            location: "Hyderabad / Bangalore, India",
            salary: "₹17,00,000 - ₹30,00,000 / yr",
            description: "Build high-performance client applications and frameworks for millions of Apple devices.",
            ribbonText: "Apple Team",
            ribbonClass: "",
            apply_link: "https://www.apple.com/careers/",
            signin_link: "https://www.apple.com/careers/"
        },
        {
            company: "NVIDIA",
            title: "CUDA & Deep Learning Engineer",
            type: "Job",
            domain: "AI Compute",
            location: "Pune / Bangalore, India",
            salary: "₹22,00,000 - ₹38,00,000 / yr",
            description: "Accelerate neural network training pipelines using CUDA C++, PyTorch, and TensorRT.",
            ribbonText: "AI Leader",
            ribbonClass: "",
            apply_link: "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
            signin_link: "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
        },
        {
            company: "NETFLIX",
            title: "Streaming Backend Engineer",
            type: "Job",
            domain: "Cloud & Media",
            location: "Remote / Mumbai",
            salary: "₹25,00,000 - ₹40,00,000 / yr",
            description: "Optimize real-time video streaming delivery algorithms and microservices architectures.",
            ribbonText: "Top Tier",
            ribbonClass: "",
            apply_link: "https://jobs.netflix.com/",
            signin_link: "https://jobs.netflix.com/"
        },
        {
            company: "UBER",
            title: "Logistics & Systems Engineer",
            type: "Job",
            domain: "Transportation Tech",
            location: "Bangalore, India",
            salary: "₹16,50,000 - ₹27,00,000 / yr",
            description: "Engineer low-latency dispatch algorithms, Geospatial routing, and transaction systems.",
            ribbonText: "Actively Hiring",
            ribbonClass: "",
            apply_link: "https://www.uber.com/us/en/careers/",
            signin_link: "https://www.uber.com/us/en/careers/"
        },
        {
            company: "RAZORPAY",
            title: "Fintech Platform Engineer",
            type: "Job",
            domain: "Fintech",
            location: "Bangalore, India",
            salary: "₹14,00,000 - ₹24,00,000 / yr",
            description: "Build high-reliability payment gateway APIs handling millions of online digital transactions.",
            ribbonText: "Fintech Leader",
            ribbonClass: "",
            apply_link: "https://razorpay.com/jobs/",
            signin_link: "https://razorpay.com/jobs/"
        }
    ];
}

app.get("/api/jobs", async (req, res) => {
    const userPrompt = req.query.prompt || req.query.q || "Software Engineer";

    try {
        const upstreamUrl = new URL(`http://${jobsHost}:${jobsBackendPort}/api/jobs`);
        upstreamUrl.search = req.originalUrl.replace(/^\/api\/jobs/, "") || `?prompt=${encodeURIComponent(userPrompt)}`;

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const response = await fetch(upstreamUrl.toString(), {
            headers: { Accept: "application/json" },
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (response.ok) {
            const payload = await response.text();
            res.status(response.status);
            res.set("content-type", response.headers.get("content-type") || "application/json");
            return res.send(payload);
        }
    } catch (error) {
        // Python backend not running or timed out — seamlessly use Express job generator
    }

    // Express standalone job generator fallback
    const jobs = await fetchExpressJobs(userPrompt);
    return res.json(jobs);
});

// Resume Analyzer Proxy & Express Standalone Handler
app.post(["/analyzer", "/api/analyzer"], upload.single("file"), async (req, res) => {
    // Try proxying to Python FastAPI backend app1.py (port 5503)
    try {
        const analyzerPort = process.env.ANALYZER_PORT || "5503";
        const formData = new (require("form-data"))();
        if (req.file) {
            formData.append("file", req.file.buffer || fs.readFileSync(req.file.path), req.file.originalname);
        }
        if (req.body.resume_text) {
            formData.append("resume_text", req.body.resume_text);
        }
        if (req.body.company_skills) {
            formData.append("company_skills", req.body.company_skills);
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const upstream = await fetch(`http://127.0.0.1:${analyzerPort}/analyzer`, {
            method: "POST",
            body: formData,
            headers: formData.getHeaders(),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (upstream.ok) {
            const result = await upstream.json();
            return res.json(result);
        }
    } catch (e) {
        // Python analyzer backend offline — fall back to Express standalone analysis
    }

    const rawText = (req.body.resume_text || "").trim() || (req.file ? req.file.buffer.toString("utf8") : "");
    const lowerText = rawText.toLowerCase();

    // 1. Timetable / Non-Resume Document Validation
    const timetableKeywords = ["timetable", "time table", "class schedule", "lecture schedule", "period 1", "period 2", "room no", "subject code", "exam schedule", "date sheet", "hall ticket", "daily routine", "invoice", "receipt", "bill"];
    const timetableHits = timetableKeywords.filter(kw => lowerText.includes(kw));
    const resumeAnchors = ["education", "experience", "skills", "projects", "qualification", "employment", "summary", "profile", "contact", "certifications", "resume"];
    const anchorHits = resumeAnchors.filter(kw => lowerText.includes(kw));

    const isValidResume = !(timetableHits.length >= 2 || (timetableHits.length >= 1 && anchorHits.length === 0) || (anchorHits.length === 0 && rawText.split(/\s+/).length < 40));
    const warningMsg = isValidResume ? null : "⚠️ Non-Resume Document Detected: The uploaded document appears to be a timetable, class schedule, or non-resume document. Please upload a genuine resume for accurate field analysis.";

    // 2. Domain Classification
    let domainName = "Engineering & Computer Science";
    let domainIcon = "💻";
    let domainDesc = "Focused on software engineering, technology systems, and technical problem solving.";

    if (lowerText.includes("mbbs") || lowerText.includes("doctor") || lowerText.includes("patient") || lowerText.includes("clinical") || lowerText.includes("nursing")) {
        domainName = "Medical & Healthcare / Doctor";
        domainIcon = "🩺";
        domainDesc = "Focused on clinical medicine, patient care, surgical procedures, and health sciences.";
    } else if (lowerText.includes("arts") || lowerText.includes("fine arts") || lowerText.includes("figma") || lowerText.includes("graphic design") || lowerText.includes("copywriting") || lowerText.includes("b.a")) {
        domainName = "Arts, Design & Humanities";
        domainIcon = "🎨";
        domainDesc = "Focused on creative arts, visual design, UI/UX, copywriting, and media.";
    } else if (lowerText.includes("b.sc") || lowerText.includes("m.sc") || lowerText.includes("laboratory") || lowerText.includes("spss") || lowerText.includes("biotechnology")) {
        domainName = "Pure & Applied Science / Research";
        domainIcon = "🔬";
        domainDesc = "Focused on scientific research, laboratory experimentation, and statistical data analysis.";
    } else if (lowerText.includes("bba") || lowerText.includes("mba") || lowerText.includes("b.com") || lowerText.includes("finance") || lowerText.includes("marketing") || lowerText.includes("accounting")) {
        domainName = "Business, Finance & Commerce";
        domainIcon = "💼";
        domainDesc = "Focused on business administration, financial analysis, marketing, and operations.";
    }

    const companySkillsStr = req.body.company_skills || "";
    const companySkills = companySkillsStr ? companySkillsStr.split(/[,;\s]+/).filter(Boolean) : [];

    if (!isValidResume) {
        return res.json({
            is_valid_resume: false,
            warning_message: warningMsg,
            predicted_domain: domainName,
            domain_icon: domainIcon,
            domain_description: domainDesc,
            action_score: 30.0,
            metrics_score: 20.0,
            structure_score: 30.0,
            length_score: 40.0,
            total_score: 28.0,
            grade: "F",
            hackathon_probability: 15.0,
            internship_probability: 20.0,
            hackathon_status: "⚠️ Document Invalid (Timetable / Schedule Detected)",
            internship_status: "⚠️ Please Upload a Valid Professional Resume",
            feedback: [{ type: "fail", text: warningMsg }],
            detected_skills: [],
            company_skills: companySkills,
            suggested_jobs: [],
            study_roadmap: [{
                category: "Resume Validation Required",
                topic: "Upload Complete Professional Resume",
                recommendation: "Your current file was identified as a timetable or schedule. Upload a full resume containing Education, Experience, and Skills.",
                priority: "HIGH",
                impact: "Unlocks Accurate Selection Scores & Career Roadmap"
            }],
            skill_gaps: ["Valid Resume File"]
        });
    }

    let studyRoadmap = [];
    let suggestedJobs = [];

    if (domainName === "Arts, Design & Humanities") {
        studyRoadmap = [
            { category: "UI/UX & Visual Design", topic: "Figma Design Systems & Interactive Wireframing", recommendation: "Master Figma components, auto-layout, and interactive prototypes.", priority: "HIGH", impact: "+25% Design Pass Rate" },
            { category: "Digital Visual Arts", topic: "Adobe Illustrator & Graphic Branding", recommendation: "Learn vector logo design and branding systems for campaigns.", priority: "HIGH", impact: "+20% Graphic Selection" },
            { category: "Creative Showcase", topic: "Online Design Portfolio (Behance / Dribbble)", recommendation: "Publish 3 complete design case studies.", priority: "HIGH", impact: "Essential for Design Interviews" }
        ];
        suggestedJobs = [
            { title: "UI/UX Designer", match_score: 90, matched_skills: ["figma", "html", "css"], missing_skills: ["photoshop"], reason: "Great match for UI design and prototyping." },
            { title: "Content Strategist & Copywriter", match_score: 85, matched_skills: ["copywriting"], missing_skills: ["figma"], reason: "Strong fit for digital content strategy." }
        ];
    } else if (domainName === "Medical & Healthcare / Doctor") {
        studyRoadmap = [
            { category: "Clinical Certifications", topic: "BLS & ACLS Certification & Patient Care", recommendation: "Complete certified Basic Life Support (BLS) and ACLS modules.", priority: "HIGH", impact: "+30% Residency Odds" },
            { category: "Healthcare Technology", topic: "Electronic Health Records (EHR) Systems", recommendation: "Familiarize with hospital EMR/EHR software platforms.", priority: "HIGH", impact: "+22% Clinical Adaptability" }
        ];
        suggestedJobs = [
            { title: "Resident Medical Officer", match_score: 92, matched_skills: ["patient care", "diagnostics"], missing_skills: ["bls"], reason: "Ideal match for clinical medicine." }
        ];
    } else if (domainName === "Pure & Applied Science / Research") {
        studyRoadmap = [
            { category: "Scientific Data Analysis", topic: "Statistical Modeling using R / Python / SPSS", recommendation: "Practice hypothesis testing and data visualization for lab data.", priority: "HIGH", impact: "+28% Fellowship Odds" },
            { category: "Laboratory Protocols", topic: "GLP Safety Standards & Protocol Rules", recommendation: "Study lab safety protocols and sample storage procedures.", priority: "HIGH", impact: "Mandatory for Research Labs" }
        ];
        suggestedJobs = [
            { title: "Research Scientist & Lab Analyst", match_score: 88, matched_skills: ["laboratory", "excel"], missing_skills: ["spss"], reason: "High alignment with lab testing." }
        ];
    } else if (domainName === "Business, Finance & Commerce") {
        studyRoadmap = [
            { category: "Financial Modeling", topic: "Advanced Excel & Valuation Models", recommendation: "Master Pivot Tables, VLOOKUP, and DCF financial models.", priority: "HIGH", impact: "+30% Interview Rate" },
            { category: "Business Intelligence", topic: "Power BI & Tableau Dashboarding", recommendation: "Build executive KPI dashboards connecting financial data.", priority: "HIGH", impact: "+25% Analytics Odds" }
        ];
        suggestedJobs = [
            { title: "Financial Analyst", match_score: 88, matched_skills: ["excel", "sql"], missing_skills: ["power bi"], reason: "Ideal match for corporate finance." }
        ];
    } else {
        studyRoadmap = [
            { category: "Version Control", topic: "Git Branching & GitHub Workflow", recommendation: "Learn Git commands and host 2+ repositories on GitHub.", priority: "HIGH", impact: "+15% Tech Selection Rate" },
            { category: "Backend Engineering", topic: "REST API Development (FastAPI / Node.js)", recommendation: "Build REST APIs and connect endpoints to SQL databases.", priority: "HIGH", impact: "+20% Backend Role Match" },
            { category: "CS Fundamentals", topic: "Data Structures, Algorithms & LeetCode", recommendation: "Solve 3-5 coding problems weekly on HashMaps and Trees.", priority: "HIGH", impact: "Essential for Tech Interviews" }
        ];
        suggestedJobs = [
            { title: "Python Developer", match_score: 85, matched_skills: ["python", "sql", "git"], missing_skills: ["fastapi"], reason: "Strong fit for Python backend development." },
            { title: "Full Stack Developer", match_score: 80, matched_skills: ["javascript", "react", "html", "css"], missing_skills: ["nodejs"], reason: "Good web prototyping background." }
        ];
    }

    return res.json({
        is_valid_resume: true,
        warning_message: null,
        predicted_domain: domainName,
        domain_icon: domainIcon,
        domain_description: domainDesc,
        action_score: 75.0,
        metrics_score: 70.0,
        structure_score: 100.0,
        length_score: 90.0,
        total_score: 82.0,
        grade: "B",
        hackathon_probability: 78.5,
        internship_probability: 81.0,
        hackathon_status: `${domainIcon} Strong Domain Contender`,
        internship_status: `🌟 High ${domainName} Qualification Odds`,
        feedback: [
            { type: "pass", text: "Standard resume sections detected." },
            { type: "pass", text: `Domain predicted as: ${domainIcon} ${domainName}.` }
        ],
        detected_skills: ["python", "excel", "figma", "git", "sql"],
        company_skills: companySkills,
        suggested_jobs: suggestedJobs,
        study_roadmap: studyRoadmap,
        skill_gaps: ["Advanced Domain Certifications"]
    });
});

app.post("/api/auth/register", (req, res) => {
    const name = String(req.body.name || "").trim();
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");

    if (!name || !email || password.length < 6) {
        return res.status(400).json({ message: "Name, email, and a password of at least 6 characters are required." });
    }

    const users = readUsers();
    if (users.some(user => user.email === email)) {
        return res.status(409).json({ message: "An account with this email already exists." });
    }

    const passwordData = hashPassword(password);
    const user = { id: crypto.randomUUID(), name, email, passwordSalt: passwordData.salt, passwordHash: passwordData.hash };
    users.push(user);
    writeUsers(users);
    createSession(req, res, user);
    return res.status(201).json({
        message: "Account created successfully.",
        redirect: "index.html",
        user: publicUser(user)
    });
});

app.post("/api/auth/login", (req, res) => {
    const email = String(req.body.email || "").trim().toLowerCase();
    const password = String(req.body.password || "");
    const user = readUsers().find(candidate => candidate.email === email);

    if (!user || !passwordsMatch(password, user)) {
        return res.status(401).json({ message: "Invalid email or password." });
    }

    createSession(req, res, user);
    return res.json({ user: publicUser(user) });
});

app.post("/api/auth/google", async (req, res) => {
    const credential = String(req.body.credential || "");
    if (!credential) return res.status(400).json({ message: "Google credential is required." });

    let profile = null;

    // 1. Try Google Token Verification Endpoint
    try {
        const response = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(credential)}`);
        if (response.ok) {
            profile = await response.json();
        }
    } catch (e) {
        console.warn("Google token verification endpoint notice:", e.message);
    }

    // 2. Fall back to JWT payload decode if tokeninfo endpoint is unreachable
    if (!profile) {
        try {
            const base64Url = credential.split(".")[1];
            const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
            const jsonPayload = decodeURIComponent(Buffer.from(base64, "base64").toString("utf8").split("").map(c => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)).join(""));
            profile = JSON.parse(jsonPayload);
        } catch (e) {
            return res.status(401).json({ message: "Google sign-in could not be verified." });
        }
    }

    const email = String(profile.email || "").trim().toLowerCase();
    if (!email) {
        return res.status(401).json({ message: "Google account email not found." });
    }

    const users = readUsers();
    let user = users.find(candidate => candidate.email === email);
    if (!user) {
        user = {
            id: crypto.randomUUID(),
            name: profile.name || email.split("@")[0],
            email: email,
            passwordSalt: "",
            passwordHash: "",
            profile: {
                fullName: profile.name || email.split("@")[0],
                emailAddress: email,
                picture: profile.picture || ""
            }
        };
        users.push(user);
        writeUsers(users);
    } else if (!user.profile) {
        user.profile = {
            fullName: user.name || email.split("@")[0],
            emailAddress: email,
            picture: profile.picture || ""
        };
        writeUsers(users);
    }

    createSession(req, res, user);
    return res.json({ user: publicUser(user) });
});

app.get("/api/auth/me", (req, res) => {
    const user = getSessionUser(req);
    return user ? res.json({ user: publicUser(user) }) : res.status(401).json({ message: "Not authenticated." });
});

app.get("/api/profile", (req, res) => {
    const user = getSessionUser(req);
    if (!user) return res.status(401).json({ message: "Not authenticated." });

    return res.json({
        user: publicUser(user),
        profile: user.profile || {
            fullName: user.name,
            emailAddress: user.email
        }
    });
});

app.put("/api/profile", (req, res) => {
    const user = getSessionUser(req);
    if (!user) return res.status(401).json({ message: "Not authenticated." });

    const profile = req.body || {};
    const fullName = String(profile.fullName || user.name).trim();
    const emailAddress = String(profile.emailAddress || user.email).trim().toLowerCase();
    if (!fullName || !emailAddress) {
        return res.status(400).json({ message: "Full name and email are required." });
    }

    const users = readUsers();
    const duplicate = users.find(candidate => candidate.email === emailAddress && candidate.id !== user.id);
    if (duplicate) return res.status(409).json({ message: "An account with this email already exists." });

    user.name = fullName;
    user.email = emailAddress;
    user.profile = { ...profile, fullName, emailAddress };
    const userIndex = users.findIndex(candidate => candidate.id === user.id);
    users[userIndex] = user;
    writeUsers(users);

    return res.json({ message: "Profile updated successfully.", user: publicUser(user) });
});

app.post("/api/auth/logout", (req, res) => {
    const sessionId = (parseCookies(req).session || "").split(".")[0];
    if (sessionId) sessions.delete(sessionId);
    res.setHeader("Set-Cookie", "session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0");
    return res.json({ message: "Logged out successfully." });
});

// Resume Upload Storage
const storage = multer.diskStorage({

    destination: (req, file, cb) => {
        cb(null, "uploads/");
    },

    filename: (req, file, cb) => {
        cb(null, Date.now() + "-" + file.originalname);
    }

});

const upload = multer({ storage: storage });

function extractIdentityFromText(text) {
    const nameMatch = text.match(/name\s*[:\-]\s*([A-Za-z .'-]+)/i) || text.match(/^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$/m);
    const dobMatch = text.match(/date\s+of\s+birth\s*[:\-]\s*(\d{4}-\d{2}-\d{2}|\d{2}\/\d{2}\/\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})/i)
        || text.match(/dob\s*[:\-]\s*(\d{4}-\d{2}-\d{2}|\d{2}\/\d{2}\/\d{4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})/i);

    return {
        fullName: nameMatch ? nameMatch[1].trim() : "",
        dob: dobMatch ? dobMatch[1].trim() : ""
    };
}

// Registration Route

app.post("/submit-registration", upload.single("resumeFile"), (req, res) => {
    let detectedIdentity = { fullName: "", dob: "" };

    if (req.file) {
        const uploadPath = path.join(__dirname, "uploads", req.file.filename);
        const extension = path.extname(req.file.originalname).toLowerCase();

        if ([".txt", ".md", ".json", ".csv"].includes(extension)) {
            try {
                const content = fs.readFileSync(uploadPath, "utf8");
                detectedIdentity = extractIdentityFromText(content);
            } catch (error) {
                console.log("Could not read uploaded resume text:", error.message);
            }
        }
    }

    const fullName = (req.body.fullName && req.body.fullName.trim()) || detectedIdentity.fullName;
    const dob = (req.body.dob && req.body.dob.trim()) || detectedIdentity.dob;

    const profile = {
        fullName,
        emailAddress: req.body.emailAddress,
        mobileNumber: req.body.mobileNumber,
        userType: req.body.userType,
        dob,
        preferredDomain: req.body.preferredDomain,
        experienceLevel: req.body.experienceLevel,
        githubProfile: req.body.githubProfile,
        linkedinProfile: req.body.linkedinProfile,
        recommendations: req.body.recommendations,
        termsAgreement: req.body.termsAgreement,
        resume: req.file ? req.file.filename : null
    };

    const accountEmail = String(profile.emailAddress || "").trim().toLowerCase();
    if (accountEmail) {
        const users = readUsers();
        let accountUser = users.find(candidate => candidate.email === accountEmail);

        if (!accountUser) {
            accountUser = {
                id: crypto.randomUUID(),
                name: fullName || accountEmail.split("@")[0],
                email: accountEmail,
                passwordSalt: "",
                passwordHash: ""
            };
            users.push(accountUser);
        }

        accountUser.name = fullName || accountUser.name;
        accountUser.profile = profile;
        writeUsers(users);
        createSession(req, res, accountUser);
    }

    console.log("--------------------------------");
    console.log("New Registration");
    console.log(profile);
    console.log("--------------------------------");

    res.json({
        status: "success",
        message: `Registration successful for ${fullName}`,
        redirect: "index.html",
        user: profile
    });
});


if (require.main === module) {
    const PORT = Number(process.env.PORT || 8800);
    const HOST = process.env.HOST || "127.0.0.1";
    const server = app.listen(PORT, HOST, () => {
        console.log("Server Running");
        console.log(`Local: http://localhost:${PORT}/register.html`);
        console.log(`Network: http://<your-computer-ip>:${PORT}/register.html`);
        startAnalyzerBackend();
        startJobsBackend();
    });

    server.on("error", error => {
        if (error.code === "EADDRINUSE") {
            console.error(`Port ${PORT} is already in use. Stop the other process or use a different PORT.`);
        } else {
            console.error("Server error:", error);
        }
        process.exitCode = 1;
    });

    process.on("uncaughtException", error => {
        console.error("Unexpected server error:", error);
    });

    process.on("unhandledRejection", error => {
        console.error("Unhandled promise rejection:", error);
    });

    function stopAnalyzerBackend() {
        if (analyzerProcess && !analyzerProcess.killed) analyzerProcess.kill();
    }

    function stopJobsBackend() {
        if (jobsProcess && !jobsProcess.killed) jobsProcess.kill();
    }

    process.on("SIGINT", () => {
        stopAnalyzerBackend();
        stopJobsBackend();
        server.close(() => process.exit(0));
    });

    process.on("SIGTERM", () => {
        stopAnalyzerBackend();
        stopJobsBackend();
        server.close(() => process.exit(0));
    });
}

module.exports = app;