require("dotenv").config();
const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const cors = require("cors");
const crypto = require("crypto");
const { spawn } = require("child_process");
const nodemailer = require("nodemailer");


const app = express();
const uploadsDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir, { recursive: true });
}

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

app.use((req, res, next) => {
    const origin = req.headers.origin || "*";
    res.setHeader("Access-Control-Allow-Origin", origin);
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, Accept, Origin");
    if (req.method === "OPTIONS") {
        return res.sendStatus(204);
    }
    if (req.url.startsWith("/api/auth")) {
        console.log(`[AUTH] ${req.method} ${req.url} from ${origin}`);
    }
    next();
});
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

const memoryUpload = multer({ storage: multer.memoryStorage() });

app.get("/api/jobs", async (req, res) => {
    try {
        const aggregatedResult = await jobAggregator.getAggregatedJobs(req.query);
        return res.json(aggregatedResult);
    } catch (error) {
        console.error("[Jobs API Error]:", error);
        return res.status(500).json({ success: false, error: "Failed to retrieve opportunities." });
    }
});

// Resume Analysis Endpoint (/api/rag/analyze & /api/analyzer & /analyzer)
app.post(["/api/rag/analyze", "/api/analyzer", "/analyzer"], memoryUpload.single("file"), async (req, res) => {
    try {
        let resumeText = req.body ? (req.body.resume_text || "") : "";
        const companySkills = req.body ? (req.body.company_skills || req.body.target_skills || "") : "";

        if (req.file && req.file.buffer) {
            const bufStr = req.file.buffer.toString("utf-8");
            const cleaned = bufStr.replace(/[^\x20-\x7E\s]/g, ' ').replace(/\s+/g, ' ').trim();
            if (cleaned.length > 20) {
                resumeText = (cleaned + "\n" + resumeText).trim();
            }
        }

        // 1. Run RAG Engine Analysis which checks marksheets and document structure
        const ragAnalysis = await ragEngine.analyzeResumeWithRag(resumeText, companySkills);

        if (ragAnalysis && ragAnalysis.is_valid_resume === false) {
            return res.json(ragAnalysis);
        }

        // 2. Try Python FastAPI Backend (app1.py on port 5503) if running
        try {
            const analyzerPort = process.env.ANALYZER_PORT || "5503";
            const formData = new (require("form-data"))();
            if (req.file) {
                formData.append("file", req.file.buffer, req.file.originalname);
            }
            if (resumeText) {
                formData.append("resume_text", resumeText);
            }
            if (companySkills) {
                formData.append("company_skills", companySkills);
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
                if (pyResult && pyResult.is_valid_resume === false) {
                    return res.json(pyResult);
                }
                return res.json({
                    ...ragAnalysis,
                    ...pyResult,
                    domain: pyResult.domain || ragAnalysis.domain,
                    predicted_domain: pyResult.predicted_domain || ragAnalysis.predicted_domain,
                    hackathon_odds: pyResult.hackathon_odds || ragAnalysis.hackathon_odds,
                    internship_odds: pyResult.internship_odds || ragAnalysis.internship_odds
                });
            }
        } catch (pyErr) {
            // Python service fallback to RAG Analysis
        }

        return res.json(ragAnalysis);
    } catch (err) {
        console.error("[Analyzer Error]:", err);
        return res.status(500).json({ error: "Resume processing error" });
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

// --- User Database & Session Management ---
const usersFile = path.join(__dirname, "users.json");
const sessions = new Map();
const sessionSecret = process.env.SESSION_SECRET || "autohire-development-secret";
const googleClientId = process.env.GOOGLE_CLIENT_ID || "985018230796-l4mivu7or4h81n86na3rpgu0c8ru53ot.apps.googleusercontent.com";

function readUsers() {
    try {
        if (!fs.existsSync(usersFile)) return [];
        return JSON.parse(fs.readFileSync(usersFile, "utf8"));
    } catch (error) {
        return [];
    }
}

function writeUsers(users) {
    try {
        fs.writeFileSync(usersFile, JSON.stringify(users, null, 2), "utf8");
    } catch (error) {
        console.error("Failed to write users.json:", error);
    }
}

function hashPassword(password, salt = crypto.randomBytes(16).toString("hex")) {
    const hash = crypto.scryptSync(password, salt, 64).toString("hex");
    return { salt, hash };
}

function passwordsMatch(password, user) {
    if (!user || !user.passwordSalt || !user.passwordHash) return false;
    const candidate = crypto.scryptSync(password, user.passwordSalt, 64);
    const stored = Buffer.from(user.passwordHash, "hex");
    return candidate.length === stored.length && crypto.timingSafeEqual(candidate, stored);
}

function parseCookies(req) {
    return Object.fromEntries((req.headers.cookie || "").split(";").filter(Boolean).map(cookie => {
        const [name, ...value] = cookie.trim().split("=");
        return [name, decodeURIComponent(value.join("="))];
    }));
}

function createSession(arg1, arg2, arg3) {
    const res = arg3 ? arg2 : arg1;
    const user = arg3 ? arg3 : arg2;
    const sessionId = crypto.randomBytes(32).toString("hex");
    const signature = crypto.createHmac("sha256", sessionSecret).update(sessionId).digest("hex");
    if (user && user.id) sessions.set(sessionId, user.id);
    if (res && res.setHeader) {
        res.setHeader("Set-Cookie", `session=${sessionId}.${signature}; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400`);
    }
    return sessionId;
}

function getSessionUser(req) {
    const value = parseCookies(req).session || "";
    const [sessionId, signature] = value.split(".");
    if (!sessionId || !signature) return null;

    const expected = crypto.createHmac("sha256", sessionSecret).update(sessionId).digest("hex");
    if (signature.length !== expected.length || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) return null;

    const userId = sessions.get(sessionId);
    return readUsers().find(user => user.id === userId) || null;
}

function publicUser(user) {
    if (!user) return null;
    const { passwordSalt, passwordHash, ...rest } = user;
    return rest;
}

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


// --- Real Email OTP & Google OAuth Security Service ---
let mailTransporter = null;
let activeMailerMode = "none"; // 'gmail', 'smtp', 'ethereal', 'console'

async function getMailTransporter() {
    if (mailTransporter) return { transporter: mailTransporter, mode: activeMailerMode };

    const smtpUser = (process.env.SMTP_USER || process.env.EMAIL_USER || "").trim();
    const smtpPass = (process.env.SMTP_PASS || process.env.EMAIL_PASS || "").replace(/\s+/g, "");
    const smtpHost = (process.env.SMTP_HOST || "").trim();
    const smtpService = (process.env.SMTP_SERVICE || "").trim().toLowerCase();

    // 1. Direct Gmail Configuration (Preferred for Gmail accounts with App Passwords)
    if (smtpUser && smtpPass && (smtpService === "gmail" || smtpUser.endsWith("@gmail.com") || smtpHost.includes("gmail"))) {
        try {
            mailTransporter = nodemailer.createTransport({
                service: "gmail",
                auth: {
                    user: smtpUser,
                    pass: smtpPass
                }
            });
            activeMailerMode = "gmail";
            console.log(`[AUTH] ✅ Real Gmail SMTP transporter initialized for: ${smtpUser}`);
            return { transporter: mailTransporter, mode: activeMailerMode };
        } catch (e) {
            console.error("[AUTH] ⚠️ Gmail SMTP transport initialization notice:", e.message);
        }
    }

    // 2. Custom SMTP Host Configuration (SendGrid, Mailgun, Brevo, AWS SES, or custom SMTP)
    if (smtpHost && smtpUser && smtpPass) {
        try {
            const port = parseInt(process.env.SMTP_PORT || "587", 10);
            mailTransporter = nodemailer.createTransport({
                host: smtpHost,
                port: port,
                secure: port === 465 || process.env.SMTP_SECURE === "true",
                auth: {
                    user: smtpUser,
                    pass: smtpPass
                },
                tls: {
                    rejectUnauthorized: false
                }
            });
            activeMailerMode = "smtp";
            console.log(`[AUTH] ✅ Real Custom SMTP transporter initialized: ${smtpHost}:${port} (${smtpUser})`);
            return { transporter: mailTransporter, mode: activeMailerMode };
        } catch (e) {
            console.error("[AUTH] ⚠️ Custom SMTP transport initialization notice:", e.message);
        }
    }

    // 3. Fallback to Ethereal Test Sandbox if real SMTP credentials are not yet configured in .env
    try {
        console.log("[AUTH] ℹ️ Real SMTP credentials not configured in .env. Initializing test sandbox...");
        const testAccount = await Promise.race([
            nodemailer.createTestAccount(),
            new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout creating test account")), 4000))
        ]);
        mailTransporter = nodemailer.createTransport({
            host: "smtp.ethereal.email",
            port: 587,
            secure: false,
            auth: {
                user: testAccount.user,
                pass: testAccount.pass
            }
        });
        activeMailerMode = "ethereal";
        console.log(`[AUTH] ℹ️ Ethereal sandbox initialized: ${testAccount.user}`);
        return { transporter: mailTransporter, mode: activeMailerMode };
    } catch (e) {
        console.warn("[AUTH] ⚠️ Ethereal account creation notice:", e.message);
        mailTransporter = {
            sendMail: async (opts) => {
                console.log(`[AUTH] 📧 [Local Dev Delivery to ${opts.to}]: Subject="${opts.subject}"`);
                return { messageId: "dev_" + Date.now() };
            }
        };
        activeMailerMode = "console";
        return { transporter: mailTransporter, mode: activeMailerMode };
    }
}

async function sendOtpEmail(recipientEmail, otpCode) {
    const { transporter, mode } = await getMailTransporter();
    const fromUser = process.env.SMTP_USER || process.env.EMAIL_USER || "security@autohire.ai";
    const fromAddress = process.env.SMTP_FROM || `"AutoHire AI Security" <${fromUser}>`;
    
    console.log(`\n======================================================`);
    console.log(`🛡️  [AUTOHIRE AI OTP] Code for ${recipientEmail}: [ ${otpCode} ]`);
    console.log(`📡 Delivery Mode: ${mode.toUpperCase()} | Time: ${new Date().toISOString()}`);
    console.log(`======================================================\n`);

    const htmlBody = `
        <div style="font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width:540px; margin:0 auto; background:#070b14; color:#f8fafc; border-radius:16px; overflow:hidden; border:1px solid rgba(255,255,255,0.12); box-shadow:0 20px 40px rgba(0,0,0,0.5);">
            <div style="padding:32px 32px 24px; background:linear-gradient(135deg, rgba(56,189,248,0.15) 0%, rgba(168,85,247,0.15) 100%); border-bottom:1px solid rgba(255,255,255,0.1);">
                <div style="font-size:24px; font-weight:800; color:#ffffff; letter-spacing:-0.03em;">🤖 Auto<span style="color:#38bdf8;">Hire AI</span></div>
                <div style="font-size:14px; color:#94a3b8; margin-top:4px;">Security & Account Verification</div>
            </div>
            <div style="padding:32px;">
                <h2 style="font-size:20px; font-weight:700; color:#f8fafc; margin-top:0;">Verify your email address</h2>
                <p style="color:#cbd5e1; font-size:15px; line-height:1.6;">You are logging into your AutoHire AI workspace via Google authentication. Please use the 6-digit verification code below to complete your login:</p>
                
                <div style="margin:28px 0; text-align:center;">
                    <div style="display:inline-block; padding:16px 32px; background:rgba(30,41,59,0.8); border:1px solid #38bdf8; border-radius:12px; font-size:32px; font-weight:800; letter-spacing:8px; color:#38bdf8; text-shadow:0 0 12px rgba(56,189,248,0.4);">
                        ${otpCode}
                    </div>
                </div>

                <div style="background:rgba(234,179,8,0.1); border-left:4px solid #eab308; padding:12px 16px; border-radius:4px; font-size:13px; color:#fef08a; line-height:1.5;">
                    ⏱️ <strong>This code is valid for 5 minutes.</strong> Do not share this code with anyone.
                </div>

                <hr style="border:none; border-top:1px solid rgba(255,255,255,0.1); margin:28px 0 20px;">
                <p style="font-size:12px; color:#64748b; margin:0; line-height:1.5;">
                    If you did not request this code, you can ignore this email. Someone may have entered your email address by mistake.
                </p>
            </div>
            <div style="padding:16px 32px; background:rgba(15,23,42,0.8); border-top:1px solid rgba(255,255,255,0.05); text-align:center; font-size:12px; color:#64748b;">
                © AutoHire AI Security Engine · All rights reserved.
            </div>
        </div>
    `;

    try {
        const info = await transporter.sendMail({
            from: fromAddress,
            to: recipientEmail,
            subject: `AutoHire AI Security - Your Verification Code is ${otpCode}`,
            text: `Your AutoHire AI verification code is ${otpCode}. Valid for 5 minutes.`,
            html: htmlBody
        });

        let previewUrl = "";
        if (mode === "ethereal" && nodemailer.getTestMessageUrl && info) {
            previewUrl = nodemailer.getTestMessageUrl(info) || "";
            if (previewUrl) console.log("📧 Ethereal Email Preview URL:", previewUrl);
        }

        const isReal = (mode === "gmail" || mode === "smtp");
        return {
            success: true,
            isRealDelivery: isReal,
            mode: mode,
            previewUrl: previewUrl,
            messageId: info.messageId || ""
        };
    } catch (e) {
        console.error(`⚠️ [AUTH] Failed to deliver OTP email via ${mode}:`, e.message);
        return {
            success: false,
            isRealDelivery: false,
            mode: mode,
            previewUrl: "",
            error: e.message
        };
    }
}

// In-Memory Pending OTP Store (tempToken => record)
const pendingOtps = new Map();

// Periodic cleanup of expired OTPs
setInterval(() => {
    const now = Date.now();
    for (const [token, data] of pendingOtps.entries()) {
        if (now > data.expiresAt) {
            pendingOtps.delete(token);
        }
    }
}, 2 * 60 * 1000);

function maskEmail(email) {
    if (!email || !email.includes("@")) return "***@***.com";
    const [user, domain] = email.split("@");
    if (user.length <= 2) {
        return `${user[0] || "*"}***@${domain}`;
    }
    return `${user[0]}***${user[user.length - 1]}@${domain}`;
}

function generateSecureOtp() {
    return crypto.randomInt(100000, 1000000).toString();
}

function hashOtp(otp, salt) {
    return crypto.createHash("sha256").update(otp + salt).digest("hex");
}

app.post("/api/auth/google", async (req, res) => {
    const credential = String(req.body.credential || "");
    if (!credential) return res.status(400).json({ message: "Google credential is required." });

    let profile = null;

    // 1. Try Google Token Verification Endpoint with 3.5s timeout
    try {
        const response = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(credential)}`, {
            signal: AbortSignal.timeout(3500)
        });
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

    // Generate secure 6-digit OTP
    const otp = generateSecureOtp();
    const salt = crypto.randomBytes(16).toString("hex");
    const hashedOtp = hashOtp(otp, salt);
    const tempToken = crypto.randomUUID();

    const googleUser = {
        id: profile.sub || crypto.randomUUID(),
        name: profile.name || email.split("@")[0],
        email: email,
        picture: profile.picture || ""
    };

    // Store in pendingOtps Map with 5-minute TTL
    pendingOtps.set(tempToken, {
        hashedOtp,
        salt,
        email,
        googleUser,
        createdAt: Date.now(),
        expiresAt: Date.now() + 5 * 60 * 1000,
        attempts: 0,
        maxAttempts: 5,
        lastResendAt: Date.now()
    });

    // Send email via Nodemailer
    const deliveryResult = await sendOtpEmail(email, otp);

    // Return response with delivery status
    return res.json({
        success: true,
        pendingOtp: true,
        tempToken: tempToken,
        email: maskEmail(email),
        delivery: {
            isRealDelivery: deliveryResult.isRealDelivery,
            mode: deliveryResult.mode,
            previewUrl: deliveryResult.previewUrl || "",
            devCode: deliveryResult.isRealDelivery ? null : otp
        }
    });

});

app.post(["/api/auth/send-otp", "/api/auth/resend-otp"], async (req, res) => {
    const tempToken = String(req.body.tempToken || "");
    if (!tempToken || !pendingOtps.has(tempToken)) {
        return res.status(400).json({ message: "This verification session has expired. Please sign in again." });
    }

    const record = pendingOtps.get(tempToken);
    const now = Date.now();

    // Rate limiting: minimum 30 seconds between resend requests
    if (now - record.lastResendAt < 30 * 1000) {
        const secondsRemaining = Math.ceil((30 * 1000 - (now - record.lastResendAt)) / 1000);
        return res.status(429).json({
            message: `Please wait ${secondsRemaining} second(s) before requesting another verification code.`
        });
    }

    // Generate new secure 6-digit OTP
    const otp = generateSecureOtp();
    const salt = crypto.randomBytes(16).toString("hex");
    record.hashedOtp = hashOtp(otp, salt);
    record.salt = salt;
    record.createdAt = now;
    record.expiresAt = now + 5 * 60 * 1000;
    record.attempts = 0;
    record.lastResendAt = now;

    const deliveryResult = await sendOtpEmail(record.email, otp);

    return res.json({
        success: true,
        message: deliveryResult.isRealDelivery 
            ? "A new 6-digit verification code has been dispatched to your Gmail inbox."
            : "A new verification code was generated (Sandbox Mode).",
        email: maskEmail(record.email),
        delivery: {
            isRealDelivery: deliveryResult.isRealDelivery,
            mode: deliveryResult.mode,
            previewUrl: deliveryResult.previewUrl || "",
            devCode: deliveryResult.isRealDelivery ? null : otp
        }
    });
});

app.post("/api/auth/verify-otp", (req, res) => {
    const tempToken = String(req.body.tempToken || "");
    const enteredOtp = String(req.body.otp || "").trim();

    if (!tempToken || !pendingOtps.has(tempToken)) {
        return res.status(400).json({ message: "This verification code has expired. Please request a new code." });
    }

    const record = pendingOtps.get(tempToken);
    const now = Date.now();

    // 1. Check expiration
    if (now > record.expiresAt) {
        pendingOtps.delete(tempToken);
        return res.status(400).json({ message: "This verification code has expired. Please request a new code." });
    }

    // 2. Check maximum attempts
    if (record.attempts >= record.maxAttempts) {
        pendingOtps.delete(tempToken);
        return res.status(429).json({ message: "Maximum verification attempts exceeded. Please request a new code." });
    }

    // 3. Hash entered OTP and verify against stored hashedOtp
    const computedHash = hashOtp(enteredOtp, record.salt);
    if (computedHash !== record.hashedOtp) {
        record.attempts++;
        if (record.attempts >= record.maxAttempts) {
            pendingOtps.delete(tempToken);
            return res.status(400).json({ message: "Maximum verification attempts exceeded. Please request a new code." });
        }
        return res.status(400).json({ message: "Invalid verification code. Please try again." });
    }

    // 4. Correct OTP -> Complete Auth, invalidate tempToken (prevent reuse)
    pendingOtps.delete(tempToken);

    const googleUser = record.googleUser;
    const email = record.email;

    const users = readUsers();
    let user = users.find(candidate => candidate.email === email);
    if (!user) {
        user = {
            id: googleUser.id || crypto.randomUUID(),
            name: googleUser.name || email.split("@")[0],
            email: email,
            passwordSalt: "",
            passwordHash: "",
            profile: {
                fullName: googleUser.name || email.split("@")[0],
                emailAddress: email,
                picture: googleUser.picture || ""
            }
        };
        users.push(user);
        writeUsers(users);
    } else if (!user.profile) {
        user.profile = {
            fullName: user.name || email.split("@")[0],
            emailAddress: email,
            picture: googleUser.picture || ""
        };
        writeUsers(users);
    }

    createSession(req, res, user);
    return res.json({
        success: true,
        message: "Authentication successful.",
        redirect: "dashboard.html",
        user: publicUser(user)
    });
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