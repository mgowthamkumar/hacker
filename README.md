# AutoHire AI - Career Intelligence Platform

AutoHire AI is an AI-powered job application, resume intelligence, and career accelerator platform. It features an automated ATS scoring engine, AI career coach, curated opportunity aggregation, and a secure **Google OAuth 2.0 + Real Email OTP Authentication System** built on **Node.js (Express)**.

---

## 🏛️ Architecture Overview

The system architecture consists of a primary Node.js web and authentication gateway interoperating with specialized Python microservices:

| Service / Component | Port | Technology | Purpose / Responsibilities |
| :--- | :--- | :--- | :--- |
| **Web & Auth Gateway** | `8800` | **Node.js Express** (`server.js`) | Web server, Google OAuth 2.0, Secure 6-Digit Email OTP, Session Management, Static UI Serving |
| **ATS Resume Analyzer** | `5503` | Python Flask (`app1.py`) | Deep resume parsing, ATS scoring, keyword matching, skill gap analysis |
| **Opportunity Aggregator** | `5501` | Python Flask (`backendreal.py`) | Curated job scrapes, internship tracking, real-time filters |
| **AI Career Coach** | `8000` | Python FastAPI (`main.py`) | FAISS vector store, RAG chatbot, contextual interview prep |

---

## 🔐 Authentication & Security Architecture

### Google OAuth 2.0 + Real Gmail OTP Flow

```
[User clicks 'Continue with Google']
           │
           ▼
[Google OAuth Sign-In Popup] ────► [Retrieves Google Credential]
           │
           ▼
[POST /api/auth/google] ────────► [Node.js Backend Validates Google Token]
                                          │
                                 ┌────────┴────────┐
                                 │ Already Verified│
                                 │    Account?     │
                                 └──┬───────────┬──┘
                                Yes │           │ No (First Time / Unverified)
                 ┌──────────────────┘           ▼
                 │                      [Generate 6-Digit Cryptographic OTP]
                 │                      (Node.js `crypto.randomInt(100000, 1000000)`)
                 │                              │
                 │                              ▼
                 │                      [Store Salted SHA-256 Hash in Memory]
                 │                      (Never plaintext; 5-min TTL)
                 │                              │
                 │                              ▼
                 │                      [Deliver via Gmail SMTP (SSL:465)]
                 │                      (Real SMTP Verification & Acceptance Check)
                 │                              │
                 │                              ▼
                 │                      [Client Shows OTP Verification Modal]
                 │                              │
                 │                              ▼
                 │                      [POST /api/auth/verify-otp]
                 │                      (Validates OTP, Invalidation on 5 fails)
                 │                              │
                 │                              ▼
                 │                      [Mark Account `isVerified = true`]
                 │                              │
                 ▼                              ▼
     [Create Authenticated Session Cookie (`session`)]
                 │
                 ▼
     [Redirect User Directly to `dashboard.html`]
```

### Security Safeguards Implemented
- **Cryptographic Randomness**: OTPs are generated on the backend using `crypto.randomInt(100000, 1000000)`.
- **Salted SHA-256 Hashing**: Plaintext OTPs are never stored, logged in plaintext, or returned in API payloads. Only a salted hash is stored.
- **Strict Single-Use & Expiry**: OTPs expire after 5 minutes and are permanently invalidated immediately upon verification or upon reaching max 5 failed attempts.
- **Rate-Limiting Cooldown**: The resend endpoint (`POST /api/auth/resend-otp`) enforces a mandatory 45-second cooldown window to prevent email flooding.
- **Strict Delivery Reporting**: If SMTP delivery fails (or credentials are not configured), the backend returns HTTP 500 (`Unable to send verification code. Please try again.`). The frontend never renders a fake OTP screen or bypasses delivery.
- **Subsequent Login Memory**: Once an account completes email verification, subsequent Google Sign-In requests with that account immediately issue a session and redirect to the dashboard without re-prompting for OTP.

---

## 🔧 Environment Configuration (`.env`)

In your `.env` file in the project root:

```ini
PORT=8800
HOST=0.0.0.0

# ----------------------------------------------------
# Real Gmail SMTP OTP Email Delivery Configuration
# ----------------------------------------------------
# 1. Open Google Account -> Security: https://myaccount.google.com/apppasswords
# 2. Make sure 2-Step Verification is enabled.
# 3. Create a new App Password (name it "AutoHire AI").
# 4. Copy the 16-character password (e.g. "abcd efgh ijkl mnop").
# 5. Paste it below for SMTP_PASS (spaces are removed automatically).
# ----------------------------------------------------
SMTP_SERVICE=gmail
SMTP_USER=mgowthamkumar472008@gmail.com
SMTP_PASS=your_16_character_app_password
SMTP_FROM="AutoHire AI Security <mgowthamkumar472008@gmail.com>"
```

### 📧 How to Obtain a Gmail App Password
1. Navigate to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification** if not already active.
3. Open [App passwords](https://myaccount.google.com/apppasswords).
4. Enter an App Name (e.g. `AutoHire AI`) and click **Create**.
5. Copy the generated **16-character password** (e.g., `abcd efgh ijkl mnop`).
6. Paste it into your `.env` file under `SMTP_PASS` without spaces (`SMTP_PASS=abcdefghijklmnop`).

---

## 🚀 Starting the Application

### Option A: Launch All Backends (Recommended)
Double-click `run-all-backends.bat` or run:
```bash
run-all-backends.bat
```

### Option B: Launch Node.js Server Standalone
```bash
node server.js
```
Open your browser and navigate to:
- **Sign In / Sign Up**: [http://localhost:8800/sign-in.html](http://localhost:8800/sign-in.html)
- **System Health**: [http://localhost:8800/health](http://localhost:8800/health)

---

## 🧪 Testing Email Delivery

You can run the interactive diagnostic tester at any time:
```bash
node test-gmail-otp.js
```
This tests your Google SMTP authentication and dispatches a test OTP email to verify your inbox delivery.
