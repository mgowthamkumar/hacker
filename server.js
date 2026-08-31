const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const cors = require("cors");
const crypto = require("crypto");
const { spawn } = require("child_process");

const app = express();
const jobAggregator = require("./job-aggregator.js");
const ragEngine = require("./rag-engine.js");
const studyPackGenerator = require("./study-pack-generator.js");
jobAggregator.startDailyScheduler();

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

// --- Applications In-Memory Table ---
const inMemoryApplications = [];

// 1. Hybrid Search API Route (/api/opportunities/search)
app.all("/api/opportunities/search", express.json(), async (req, res) => {
    try {
        const query = req.query.q || req.query.prompt || (req.body && (req.body.q || req.body.prompt)) || "";
        const category = req.query.category || req.query.cat || (req.body && req.body.category) || "all";
        const page = parseInt(req.query.page || (req.body && req.body.page) || 1, 10);
        const limit = parseInt(req.query.limit || (req.body && req.body.limit) || 20, 10);

        const result = await ragEngine.searchOpportunities(query, category, page, limit);
        return res.json(result);
    } catch (error) {
        console.error("[Opportunities Search Error]:", error);
        const aggregatedResult = await jobAggregator.getAggregatedJobs(req.query);
        return res.json(aggregatedResult);
    }
});

app.get("/api/jobs", async (req, res) => {
    try {
        const aggregatedResult = await jobAggregator.getAggregatedJobs(req.query);
        return res.json(aggregatedResult);
    } catch (error) {
        console.error("[Jobs API Error]:", error);
        return res.status(500).json({ success: false, error: "Failed to retrieve opportunities." });
    }
});

// 2. Native Application Handler Route (/api/applications/apply)
app.post("/api/applications/apply", express.json(), async (req, res) => {
    try {
        const {
            opportunity_id,
            opportunity_title,
            organization,
            candidate_name,
            candidate_email,
            resume_text,
            portfolio_url,
            cover_note,
            apply_mode
        } = req.body || {};

        if (!candidate_name || !candidate_email) {
            return res.status(400).json({ success: false, error: "Candidate Name and Candidate Email are required." });
        }

        const applicationId = "app_" + Date.now() + "_" + Math.random().toString(36).substr(2, 6);
        const isNative = apply_mode !== "external";

        const applicationRecord = {
            id: applicationId,
            opportunity_id: opportunity_id || "gen_opp_" + Date.now(),
            opportunity_title: opportunity_title || "General Application",
            organization: organization || "Partner Employer",
            candidate_name: candidate_name.trim(),
            candidate_email: candidate_email.trim(),
            resume_text: (resume_text || "").slice(0, 500),
            portfolio_url: portfolio_url || "",
            cover_note: cover_note || "Interested in pursuing this opportunity.",
            mode: isNative ? "Mode A (Native Direct Post)" : "Mode B (Assisted Auto-Apply)",
            status: "Submitted",
            created_at: new Date().toISOString()
        };

        inMemoryApplications.unshift(applicationRecord);
        console.log(`[AutoHire Applications] New ${applicationRecord.mode} created for ${candidate_name} -> ${opportunity_title}`);

        return res.json({
            success: true,
            message: `Application submitted successfully via AutoHire! (${applicationRecord.mode})`,
            application: applicationRecord,
            redirect_url: isNative ? null : (req.body.apply_url || "https://google.com/search?q=" + encodeURIComponent(organization + " " + opportunity_title))
        });
    } catch (err) {
        console.error("[Application API Error]:", err);
        return res.status(500).json({ success: false, error: "Failed to process application." });
    }
});

// 3. Application Tracking Status Route (/api/applications/status)
app.get("/api/applications/status", (req, res) => {
    const email = (req.query.email || "").toString().toLowerCase();
    let apps = inMemoryApplications;
    if (email) {
        apps = apps.filter(a => a.candidate_email.toLowerCase() === email);
    }

    return res.json({
        success: true,
        total: apps.length,
        applications: apps
    });
});

// 4. AI Tailored Cover Letter Generator Helper (/api/applications/cover-letter)
app.post("/api/applications/cover-letter", express.json(), (req, res) => {
    const { opportunity_title, organization, candidate_name, key_skills } = req.body || {};
    const name = candidate_name || "Applicant";
    const title = opportunity_title || "Software Engineering Role";
    const org = organization || "your organization";
    const skills = Array.isArray(key_skills) ? key_skills.join(", ") : (key_skills || "Fullstack Software Engineering, Python, React, REST APIs");

    const letter = `Dear Hiring Team at ${org},

I am writing to express my strong enthusiasm for the ${title} position. With verified expertise in ${skills}, I have engineered robust systems and delivered scalable technical solutions.

My background aligns directly with the core competencies expected at ${org}. I am eager to leverage my technical problem-solving capabilities to drive measurable impact.

Thank you for your time and consideration.

Best regards,  
${name}`;

    return res.json({
        success: true,
        cover_letter: letter
    });
});

// --- RAG (Retrieval-Augmented Generation) API Endpoints ---
app.all("/api/rag/query", express.json(), async (req, res) => {
    const query = req.query.q || req.query.prompt || (req.body && (req.body.q || req.body.prompt)) || "Which jobs match my skills?";
    const category = req.query.category || (req.body && req.body.category) || "all";
    const result = await ragEngine.answerQueryWithRag(query, category);
    return res.json(result);
});

app.get("/api/rag/search", async (req, res) => {
    const query = req.query.q || req.query.prompt || "";
    const k = parseInt(req.query.k || 5, 10);
    const category = req.query.category || "all";
    const matches = ragEngine.similaritySearch(query, k, category);
    return res.json({
        success: true,
        query,
        count: matches.length,
        results: matches.map(m => ({
            id: m.document.id,
            category: m.document.category,
            type: m.document.type,
            title: m.document.metadata.title || m.document.id,
            similarityScore: Math.round(m.similarityScore * 100) + "%",
            metadata: m.document.metadata
        }))
    });
});

// --- Combined Resume Analyzer Endpoint (Python FastAPI + Node RAG Engine) ---
app.post(["/api/rag/analyze", "/analyzer", "/api/analyzer"], upload.single("file"), async (req, res) => {
    const resumeText = (req.body && req.body.resume_text) || (req.file ? req.file.buffer.toString("utf8") : "") || "";
    const targetSkills = (req.body && (req.body.company_skills || req.body.target_skills)) || "";

    // 1. Run RAG Vector Grounded Analysis
    const ragAnalysis = await ragEngine.analyzeResumeWithRag(resumeText, targetSkills);

    // 2. Attempt Python FastAPI Backend (app1.py on port 5503) & merge results
    try {
        const analyzerPort = process.env.ANALYZER_PORT || "5503";
        const formData = new (require("form-data"))();
        if (req.file) {
            formData.append("file", req.file.buffer || fs.readFileSync(req.file.path), req.file.originalname);
        }
        if (resumeText) {
            formData.append("resume_text", resumeText);
        }
        if (targetSkills) {
            formData.append("company_skills", targetSkills);
        }

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3500);

        const upstream = await fetch(`http://127.0.0.1:${analyzerPort}/analyzer`, {
            method: "POST",
            body: formData,
            headers: formData.getHeaders(),
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (upstream.ok) {
            const pyResult = await upstream.json();
            const merged = {
                ...ragAnalysis,
                ...pyResult,
                domain: pyResult.domain || ragAnalysis.domain,
                predicted_domain: pyResult.predicted_domain || ragAnalysis.predicted_domain,
                hackathon_odds: pyResult.hackathon_odds || ragAnalysis.hackathon_odds,
                internship_odds: pyResult.internship_odds || ragAnalysis.internship_odds,
                overall_score: pyResult.overall_score || ragAnalysis.overall_score,
                metrics: pyResult.metrics || ragAnalysis.metrics,
                roadmap: (pyResult.roadmap && pyResult.roadmap.length > 0) ? pyResult.roadmap : ragAnalysis.roadmap,
                study_roadmap: (pyResult.study_roadmap && pyResult.study_roadmap.length > 0) ? pyResult.study_roadmap : ragAnalysis.study_roadmap,
                job_matches: (pyResult.job_matches && pyResult.job_matches.length > 0) ? pyResult.job_matches : ragAnalysis.job_matches,
                suggested_jobs: (pyResult.suggested_jobs && pyResult.suggested_jobs.length > 0) ? pyResult.suggested_jobs : ragAnalysis.suggested_jobs,
                verbatim_facts: pyResult.verbatim_facts || ragAnalysis.verbatim_facts,
                taxonomy_analysis: pyResult.taxonomy_analysis || ragAnalysis.taxonomy_analysis,
                competency_audit: pyResult.competency_audit || ragAnalysis.competency_audit,
                precision_study_manual: pyResult.precision_study_manual || ragAnalysis.precision_study_manual,
                compiled_typeset_manual: pyResult.compiled_typeset_manual || ragAnalysis.compiled_typeset_manual,
                feedback: Array.from(new Set([...(ragAnalysis.feedback || []), ...(pyResult.feedback ? pyResult.feedback.map(f => typeof f === 'string' ? f : f.text) : [])]))
            };
            return res.json(merged);
        }
    } catch (e) {
        // Python backend offline — return complete combined RAG analysis
    }

    return res.json(ragAnalysis);
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
    const HOST = process.env.HOST || "0.0.0.0";
    const server = app.listen(PORT, HOST, () => {
        console.log("Server Running");
        console.log(`Local: http://localhost:${PORT}/register.html`);
        console.log(`Network Mobile: http://0.0.0.0:${PORT}/register.html`);
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