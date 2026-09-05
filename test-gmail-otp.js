/**
 * AutoHire AI - Real Gmail SMTP OTP Delivery Tester
 * Usage: node test-gmail-otp.js [optional-recipient-email]
 */

require("dotenv").config({ override: true });
const nodemailer = require("nodemailer");

async function testGmailDelivery() {
    const smtpUser = (process.env.SMTP_USER || "").trim();
    const smtpPass = (process.env.SMTP_PASS || "").replace(/\s+/g, "");
    const recipient = process.argv[2] || smtpUser;

    console.log("\n=======================================================");
    console.log("🚀 AutoHire AI - Real Gmail SMTP Delivery Diagnostic");
    console.log("=======================================================");
    console.log(`📧 Configured Sender Account : ${smtpUser || "(NOT SET)"}`);
    console.log(`🎯 Recipient Inbox           : ${recipient || "(NOT SET)"}`);
    console.log(`🔑 Password Status           : ${smtpPass ? `CONFIGURED (${smtpPass.length} chars)` : "❌ EMPTY / NOT CONFIGURED"}`);
    console.log("=======================================================\n");

    if (!smtpUser || !smtpPass) {
        console.error("❌ ERROR: SMTP credentials are not configured in your .env file!");
        console.log("\n👉 How to enable real Gmail delivery in 60 seconds:");
        console.log("1. Go to Google Account Security: https://myaccount.google.com/apppasswords");
        console.log("2. Create an App Password with the name 'AutoHire AI'.");
        console.log("3. Copy the 16-character password provided by Google.");
        console.log("4. Open .env in your project folder and set:");
        console.log("   SMTP_PASS=your_16_character_password");
        console.log("5. Run this test again: node test-gmail-otp.js\n");
        process.exit(1);
    }

    console.log("📡 Step 1: Connecting to Google SMTP (smtp.gmail.com:465 SSL)...");
    const transporter = nodemailer.createTransport({
        host: "smtp.gmail.com",
        port: 465,
        secure: true,
        auth: {
            user: smtpUser,
            pass: smtpPass
        },
        connectionTimeout: 10000
    });

    try {
        await transporter.verify();
        console.log("✅ Step 1 SUCCESS: Google authenticated your account successfully!\n");
    } catch (err) {
        console.error("❌ Step 1 FAILED: Could not authenticate with Google SMTP.");
        console.error("Google Server Error:", err.message);
        if (err.message.includes("Username and Password not accepted") || err.message.includes("535")) {
            console.log("\n💡 Solution: Google requires a 16-character 'App Password', not your regular login password.");
            console.log("Generate one here: https://myaccount.google.com/apppasswords\n");
        }
        process.exit(1);
    }

    const testOtp = String(Math.floor(100000 + Math.random() * 900000));
    console.log(`📨 Step 2: Sending real OTP verification email [ ${testOtp} ] to ${recipient}...`);

    try {
        const info = await transporter.sendMail({
            from: `"AutoHire AI Security" <${smtpUser}>`,
            to: recipient,
            subject: `AutoHire AI Verification Code: ${testOtp}`,
            text: `Your AutoHire AI verification code is ${testOtp}. This code is valid for 5 minutes.`,
            html: `
                <div style="font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width:520px; margin:0 auto; background:#070b14; color:#f8fafc; border-radius:16px; overflow:hidden; border:1px solid rgba(255,255,255,0.15); box-shadow:0 20px 40px rgba(0,0,0,0.5);">
                    <div style="padding:28px; background:linear-gradient(135deg, rgba(56,189,248,0.2) 0%, rgba(168,85,247,0.2) 100%); border-bottom:1px solid rgba(255,255,255,0.1);">
                        <div style="font-size:22px; font-weight:800; color:#ffffff;">🤖 Auto<span style="color:#38bdf8;">Hire AI</span></div>
                        <div style="font-size:13px; color:#94a3b8; margin-top:4px;">Security & Account Verification</div>
                    </div>
                    <div style="padding:28px;">
                        <h2 style="font-size:18px; font-weight:700; color:#f8fafc; margin-top:0;">Your 6-Digit Verification Code</h2>
                        <p style="color:#cbd5e1; font-size:14px; line-height:1.5;">Use the security code below to complete your sign-in to AutoHire AI:</p>
                        <div style="margin:24px 0; text-align:center;">
                            <div style="display:inline-block; padding:14px 28px; background:rgba(30,41,59,0.9); border:1px solid #38bdf8; border-radius:10px; font-size:32px; font-weight:800; letter-spacing:8px; color:#38bdf8;">
                                ${testOtp}
                            </div>
                        </div>
                        <p style="font-size:12px; color:#94a3b8; margin:0;">⏱️ Valid for 5 minutes. Do not share this code with anyone.</p>
                    </div>
                </div>
            `,
            headers: {
                "X-Priority": "1",
                "Importance": "high"
            }
        });

        console.log("🎉 SUCCESS! OTP email was dispatched directly to Google's mail server!");
        console.log(`📬 Message ID : ${info.messageId}`);
        console.log(`📡 SMTP Reply : ${info.response}`);
        console.log(`\n👉 Check the inbox for ${recipient} (also check Primary / Spam tab if first time).`);
    } catch (err) {
        console.error("❌ Step 2 FAILED: Error dispatching email:", err.message);
        process.exit(1);
    }
}

testGmailDelivery();
