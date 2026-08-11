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

function startJobsBackend() {
    const pythonCommand = process.env.PYTHON_COMMAND || (process.platform === "win32" ? "python" : "python3");
    jobsProcess = spawn(pythonCommand, [path.join(__dirname, "backendreal.py")], {
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

app.get("/api/jobs", async (req, res) => {
    try {
        const jobsBackendPort = process.env.JOBS_BACKEND_PORT || "5501";
        const upstreamUrl = new URL(`http://127.0.0.1:${jobsBackendPort}/api/jobs`);
        upstreamUrl.search = req.originalUrl.replace(/^\/api\/jobs/, "") || "";

        const response = await fetch(upstreamUrl.toString(), {
            headers: {
                Accept: "application/json"
            }
        });

        const payload = await response.text();
        res.status(response.status);
        res.set("content-type", response.headers.get("content-type") || "application/json");
        res.send(payload);
    } catch (error) {
        res.status(502).json({
            error: "Jobs backend unavailable",
            detail: error.message
        });
    }
});

app.get("/create-account", (req, res) => {
    res.sendFile(path.join(__dirname, "create-account.html"));
});

const usersFile = path.join(__dirname, "users.json");
const sessions = new Map();
const sessionSecret = process.env.SESSION_SECRET || "autohire-development-secret";
const googleClientId = process.env.GOOGLE_CLIENT_ID || "869568422226-14fcbs1j1esdl1f0phijfhoude5il7qk.apps.googleusercontent.com";
fs.mkdirSync(path.join(__dirname, "uploads"), { recursive: true });

function readUsers() {
    try {
        return JSON.parse(fs.readFileSync(usersFile, "utf8"));
    } catch (error) {
        return [];
    }
}

function writeUsers(users) {
    fs.writeFileSync(usersFile, JSON.stringify(users, null, 2));
}

function hashPassword(password, salt = crypto.randomBytes(16).toString("hex")) {
    const hash = crypto.scryptSync(password, salt, 64).toString("hex");
    return { salt, hash };
}

function passwordsMatch(password, user) {
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

function createSession(req, res, user) {
    const sessionId = crypto.randomBytes(32).toString("hex");
    const signature = crypto.createHmac("sha256", sessionSecret).update(sessionId).digest("hex");
    sessions.set(sessionId, user.id);
    const isHttps = req.secure || req.headers["x-forwarded-proto"] === "https";
    const cookieOptions = `HttpOnly; SameSite=${isHttps ? "None" : "Lax"}; Path=/; Max-Age=86400${isHttps ? "; Secure" : ""}`;
    res.setHeader("Set-Cookie", `session=${sessionId}.${signature}; ${cookieOptions}`);
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
    return {
        id: user.id,
        name: user.name,
        email: user.email,
        profile: user.profile || null
    };
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

app.post("/api/auth/google", async (req, res) => {
    const credential = String(req.body.credential || "");
    if (!credential) return res.status(400).json({ message: "Google credential is required." });

    try {
        const response = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(credential)}`);
        if (!response.ok) return res.status(401).json({ message: "Google sign-in could not be verified." });

        const profile = await response.json();
        if (profile.aud !== googleClientId || profile.email_verified !== "true") {
            return res.status(401).json({ message: "Invalid or unverified Google account." });
        }

        const users = readUsers();
        let user = users.find(candidate => candidate.email === profile.email.toLowerCase());
        if (!user) {
            user = {
                id: crypto.randomUUID(),
                name: profile.name || profile.email.split("@")[0],
                email: profile.email.toLowerCase(),
                passwordSalt: "",
                passwordHash: ""
            };
            users.push(user);
            writeUsers(users);
        }

        createSession(req, res, user);
        return res.json({ user: publicUser(user) });
    } catch (error) {
        console.error("Google sign-in error:", error.message);
        return res.status(502).json({ message: "Google sign-in service is unavailable." });
    }
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