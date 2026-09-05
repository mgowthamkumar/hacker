/**
 * Diagnostic script to inspect Node.js email configuration and test SMTP connection
 */

require("dotenv").config({ override: true });
const nodemailer = require("nodemailer");
const path = require("path");
const fs = require("fs");

function maskEmail(str) {
    if (!str || typeof str !== "string") return "(NOT SET)";
    const at = str.indexOf("@");
    if (at === -1) return str.length > 4 ? str[0] + "****" + str.slice(-1) : "****";
    const user = str.slice(0, at);
    const domain = str.slice(at);
    if (user.length <= 2) return user[0] + "****" + domain;
    return user[0] + "****" + user[user.length - 1] + domain;
}

async function runDiagnostic() {
    console.log("=========================================");
    console.log("🔍 Node.js Email Diagnostic Inspection");
    console.log("=========================================\n");

    // 1. Email library
    console.log("1. Email library:", "Nodemailer", "(version: " + require("nodemailer/package.json").version + ")");

    // 2. Email provider
    const service = process.env.SMTP_SERVICE || "gmail";
    console.log("2. Configured provider:", service);

    // 3. SMTP host
    const host = process.env.SMTP_HOST || (service === "gmail" ? "smtp.gmail.com" : "(not set)");
    console.log("3. SMTP Host:", host);

    // 4. SMTP port
    const port = parseInt(process.env.SMTP_PORT || (service === "gmail" ? "587" : "587"), 10);
    console.log("4. SMTP Port:", port);

    // 6 & 7. Check .env loading
    const envPath = path.join(process.cwd(), ".env");
    const envExists = fs.existsSync(envPath);
    console.log("7. .env file found:", envExists, "at", envPath);

    // 8. SMTP username
    const smtpUser = (process.env.SMTP_USER || process.env.SMTP_USERNAME || process.env.EMAIL_USER || "").trim();
    console.log("8. SMTP Username:", smtpUser ? `PRESENT (${maskEmail(smtpUser)})` : "MISSING");

    // 9. SMTP password
    const smtpPass = (process.env.SMTP_PASS || process.env.SMTP_PASSWORD || process.env.EMAIL_PASS || "").replace(/\s+/g, "");
    console.log("9. SMTP Password:", smtpPass ? `PRESENT (${smtpPass.length} chars)` : "MISSING (EMPTY)");

    // 5. SMTP auth configured
    const authConfigured = Boolean(smtpUser && smtpPass);
    console.log("5. Is SMTP auth configured:", authConfigured);

    // 10. EMAIL_FROM / SMTP_FROM
    const emailFrom = process.env.SMTP_FROM || process.env.EMAIL_FROM || "";
    console.log("10. EMAIL_FROM configured:", emailFrom ? `PRESENT (${maskEmail(emailFrom)})` : "MISSING");

    // 11 & 12. Test transporter connection
    console.log("\n--- Testing SMTP Connection ---");
    if (!smtpUser || !smtpPass) {
        console.log("❌ Result: SMTP configuration is incomplete.");
        console.log("Missing required credentials: " + (!smtpUser ? "SMTP_USER " : "") + (!smtpPass ? "SMTP_PASS" : ""));
        return;
    }

    const isPort465 = port === 465;
    const transporter = nodemailer.createTransport({
        host: host,
        port: port,
        secure: isPort465,
        requireTLS: !isPort465,
        auth: {
            user: smtpUser,
            pass: smtpPass
        },
        connectionTimeout: 8000
    });

    try {
        await transporter.verify();
        console.log("✅ Transporter verify(): SUCCESS - SMTP connection & authentication passed!");
    } catch (err) {
        console.log("❌ Transporter verify(): FAILED");
        console.log("Error Name:", err.name);
        console.log("Error Code:", err.code || "(none)");
        console.log("Error Command:", err.command || "(none)");
        console.log("Error Response:", err.response || "(none)");
        console.log("Error Message:", err.message);
    }
}

runDiagnostic();
