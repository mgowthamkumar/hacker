# AutoHire AI - Next-Gen Career Intelligence Platform

AutoHire AI is an enterprise-grade AI-powered job application, resume intelligence, and career accelerator platform. It features an automated ATS scoring engine, AI conversational career coach, curated opportunity aggregation, and a secure **Google OAuth 2.0 + Email OTP Authentication System** built on **Python FastAPI**.

---

## 🏛️ Architecture Overview

The backend architecture consists of a primary web and authentication gateway (FastAPI) interoperating seamlessly with specialized Python microservices:

| Service / Component | Port | Technology | Purpose / Responsibilities | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Gateway & Auth** | `8800` | **Python FastAPI** | Core Web Server, Google OAuth 2.0, Secure Email OTP, Session Management, SQLite ORM, Static UI Serving | **Migrated from Node.js** |
| **ATS Resume Analyzer** | `5503` | Python Flask (`app1.py`) | Deep resume parsing, ATS scoring, keyword matching, skill gap analysis | **Preserved (Untouched)** |
| **Opportunity Aggregator** | `5501` | Python Flask (`backendreal.py`) | Curated job scrapes, internship tracking, real-time filters | **Preserved (Untouched)** |
| **AI Career Coach** | `8000` | Python FastAPI (`main.py`) | FAISS vector store, RAG chatbot, contextual interview prep | **Preserved (Untouched)** |

> **Crucial Guarantee**: The migration from `server.js` to FastAPI was strictly scoped to replace the Node.js web server on port `8800`. The existing Python services (`app1.py`, `backendreal.py`, `main.py`) are fully preserved and remain completely functional.

---

## 🔐 Authentication & Security Architecture

### Google OAuth 2.0 + Cryptographic Backend OTP Flow

```
[User clicks 'Continue with Google']
           │
           ▼
[Google OAuth Sign-In Popup] ────► [Retrieves Google Credential]
           │
           ▼
[POST /api/auth/google] ────────► [FastAPI Backend Validates Google Token]
                                          │
                                 ┌────────┴────────┐
                                 │ Already Verified│
                                 │    Account?     │
                                 └──┬───────────┬──┘
                                Yes │           │ No (First Time / Unverified)
                 ┌──────────────────┘           ▼
                 │                      [Generate 6-Digit Cryptographic OTP]
                 │                      (Python `secrets.randbelow`)
                 │                              │
                 │                              ▼
                 │                      [Store Salted HMAC-SHA256 Hash]
                 │                      (Never plaintext; 5-min TTL)
                 │                              │
                 │                              ▼
                 │                      [Deliver via Gmail SMTP (SSL:465)]
                 │                      (HTML Template with AutoHire AI Branding)
                 │                              │
                 │                              ▼
                 │                      [Client Shows OTP Verification Modal]
                 │                              │
                 │                              ▼
                 │                      [POST /api/auth/verify-otp]
                 │                      (Validates OTP, Invalidation on 5 fails)
                 │                              │
                 │                              ▼
                 │                      [Mark Account `is_verified = True`]
                 │                              │
                 ▼                              ▼
     [Create Signed HTTP-Only Session Cookie (`session_token`)]
                 │
                 ▼
     [Redirect User Directly to `dashboard.html`]
```

### Security Safeguards Implemented
- **Cryptographic Randomness**: OTPs are generated using `secrets.randbelow(900000) + 100000` (true CSPRNG), eliminating predictable PRNG sequences.
- **Salted HMAC-SHA256 Hashing**: Plaintext OTPs are never stored in `autohire.db`, never printed in server logs, and never returned in API payloads. Only a salted HMAC hash is kept.
- **Strict Single-Use & Expiry**: OTPs expire after 5 minutes (`OTP_EXPIRE_MINUTES=5`) and are permanently marked `is_used=True` immediately upon verification or upon reaching max 5 failed attempts.
- **Rate-Limiting Cooldown**: The resend endpoint (`POST /api/auth/resend-otp`) enforces a mandatory 45-second cooldown window to prevent email flooding or spamming.
- **Strict Delivery Reporting**: If SMTP fails (e.g. invalid credentials or network drop), the backend returns HTTP 500 (`Unable to send verification code. Please try again.`). The frontend never renders a fake OTP screen or bypasses delivery.
- **Subsequent Login Memory**: Once an account completes email verification, subsequent Google Sign-In requests with that account immediately issue a session and redirect to the dashboard without re-prompting for OTP.

---

## 📋 Endpoint Mapping: Node.js (`server.js`) ➔ FastAPI (`backend/app/`)

| JavaScript Node.js Endpoint | New Python FastAPI Endpoint | Module Handler | Description |
| :--- | :--- | :--- | :--- |
| `POST /api/auth/google` | `POST /api/auth/google` | `routes/auth.py:google_auth` | Google OAuth token verification, account lookup, and OTP challenge dispatch |
| `POST /api/auth/verify-otp` | `POST /api/auth/verify-otp` | `routes/auth.py:verify_otp` | Constant-time HMAC OTP validation and session token generation |
| `POST /api/auth/resend-otp` | `POST /api/auth/resend-otp` | `routes/auth.py:resend_otp` | 45-second rate-limited OTP regeneration and SMTP dispatch |
| `POST /api/auth/login` | `POST /api/auth/login` | `routes/auth.py:login` | Email/password login with verified account check |
| `POST /api/auth/register` | `POST /api/auth/register` | `routes/auth.py:register` | New user registration and automatic verification dispatch |
| `POST /api/auth/logout` | `POST /api/auth/logout` | `routes/auth.py:logout` | Clears HTTP-only signed session cookie |
| `GET /api/auth/me` | `GET /api/auth/me` | `routes/auth.py:get_current_user_info` | Returns currently authenticated user details |
| `GET /api/auth/smtp-status` | `GET /api/auth/smtp-status` | `routes/auth.py:smtp_status` | Returns Gmail SMTP readiness and configuration status |
| `POST /api/auth/configure-smtp` | `POST /api/auth/configure-smtp` | `routes/auth.py:configure_smtp` | Dynamically test and update SMTP credentials |
| `GET /api/profile` | `GET /api/profile` | `routes/profile.py:get_profile` | Retrieves current user profile data |
| `PUT /api/profile` | `PUT /api/profile` | `routes/profile.py:update_profile` | Updates profile (skills, resume, preferences) |
| `GET /api/jobs` | `GET /api/jobs` | `routes/jobs.py:get_jobs` | Serves paginated aggregated opportunities |
| `GET /api/opportunities/search`| `GET /api/opportunities/search`| `routes/jobs.py:search_opportunities`| Full-text and keyword job search |
| `GET /` | `GET /` | `main.py:root` | Serves `index.html` static landing page |
| `GET /health` | `GET /health` | `main.py:health_check` | System diagnostic and health check |

---

## ⚙️ Prerequisites & Installation

### Requirements
- **Python 3.10+** (Tested on Python 3.11 / 3.12)
- **pip** package manager

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

The `requirements.txt` includes:
```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.28
pydantic>=2.6.0
python-dotenv>=1.0.1
requests>=2.31.0
google-auth>=2.28.0
itsdangerous>=2.1.2
jinja2>=3.1.3
email-validator>=2.1.1
httpx>=0.27.0
```

---

## 🔧 Environment Configuration (`.env`)

Create or update your `.env` in the project root:

```ini
# AutoHire AI Security Configuration
PORT=8800
SECRET_KEY=autohire-ai-super-secret-production-key-2026-xyz
SESSION_SECRET=autohire-ai-session-cookie-secret-key-2026-xyz
CORS_ORIGINS=*

# Google OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=335276361730-8quu28l2632d4vj683j35c0p9533f8j9.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_google_client_secret_here

# Gmail SMTP Configuration (Port 465 SSL)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=mgowthamkumar472008@gmail.com
SMTP_PASS=your_16_character_google_app_password
SMTP_FROM="AutoHire AI Security <mgowthamkumar472008@gmail.com>"

# Verification Settings
OTP_EXPIRE_MINUTES=5
OTP_MAX_ATTEMPTS=5
OTP_RESEND_COOLDOWN_SECONDS=45

# Database Settings
DATABASE_URL=sqlite:///./autohire.db
```

### 📧 How to Obtain a Gmail App Password
1. Navigate to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification** if not already active.
3. Search for **"App passwords"** in the top search bar (or go to `Security -> 2-Step Verification -> App passwords`).
4. Enter an App Name (e.g. `AutoHire AI Backend`) and click **Create**.
5. Copy the generated **16-character password** (e.g., `abcd efgh ijkl mnop`).
6. Paste it into your `.env` file under `SMTP_PASS` without spaces (`SMTP_PASS=abcdefghijklmnop`).

---

## 🚀 Starting the Application

### Option A: Launch All Backends (Recommended)
Double-click `run-all-backends.bat` or run in terminal:
```bash
run-all-backends.bat
```
This script launches:
1. `backendreal.py` (Port 5501 - Opportunities Tracker)
2. `app1.py` (Port 5503 - ATS Resume Analyzer)
3. `main.py` (Port 8000 - AI Chatbot)
4. `run_server.py` (Port 8800 - **FastAPI Web & Auth Gateway**)

### Option B: Launch FastAPI Auth Gateway Standalone
```bash
python run_server.py
```
Open your browser and navigate to:
- **Sign In / Sign Up**: [http://localhost:8800/sign-in.html](http://localhost:8800/sign-in.html)
- **Interactive Swagger API Docs**: [http://localhost:8800/docs](http://localhost:8800/docs)
- **Redoc Interactive Specs**: [http://localhost:8800/redoc](http://localhost:8800/redoc)
- **System Health**: [http://localhost:8800/health](http://localhost:8800/health)

---

## 🧪 Automated Testing

The project includes an end-to-end integration test suite validating the entire authentication cycle:

```bash
python scratch/test_fastapi_auth.py
```

### Verified Test Suite Capabilities:
- ✅ **Test 1: Health Check** (`GET /health`)
- ✅ **Test 2: Static Page Delivery** (`sign-in.html`, `dashboard.html`)
- ✅ **Test 3: Jobs API Integration** (`GET /api/jobs` from 299 curated postings)
- ✅ **Test 4: SMTP Diagnostics** (`GET /api/auth/smtp-status`)
- ✅ **Test 5: CSPRNG OTP Generation** (`secrets.randbelow`) & HMAC-SHA256 salted storage
- ✅ **Test 6: Invalid OTP Rejection** (Strict HTTP 400 rejection)
- ✅ **Test 7: Brute-Force Defense** (Auto-invalidation on 5 failed attempts)
- ✅ **Test 8: Cooldown Rate-Limiting** (45s window enforced on `resend-otp`)
- ✅ **Test 9: OTP Verification & Cookie Issuance** (Session establishment)
- ✅ **Test 10: Subsequent Login Memory** (Zero OTP required on returning verified accounts)
- ✅ **Test 11: Clean Session Termination** (`POST /api/auth/logout`)

---

## 📂 Project Structure

```
hacker/
├── backend/                        # Python FastAPI Backend Architecture
│   └── app/
│       ├── __init__.py
│       ├── config.py               # Pydantic Settings and .env reader
│       ├── database.py             # SQLite engine, ORM session, data migration
│       ├── main.py                 # FastAPI application root, static mounts & CORS
│       ├── auth/
│       │   ├── google_oauth.py     # Google token verification
│       │   ├── otp_service.py      # OTP lifecycle (create, hash, verify, cooldown)
│       │   └── session.py          # Signed HTTP-only session serializer
│       ├── models/
│       │   ├── user.py             # SQLAlchemy User model
│       │   └── otp.py              # SQLAlchemy OTPRecord model
│       ├── routes/
│       │   ├── auth.py             # Auth endpoints (google, verify, resend, logout)
│       │   ├── jobs.py             # Opportunity listings & search endpoints
│       │   └── profile.py          # User profile management endpoints
│       ├── schemas/
│       │   └── auth.py             # Pydantic request & response validation schemas
│       ├── services/
│       │   └── email_service.py    # SSL Port 465 SMTP delivery & HTML template
│       └── utils/
│           └── security.py         # CSPRNG, constant-time compare, masking
├── autohire.db                     # SQLite production database
├── aggregated_opportunities.json   # 299 curated jobs & opportunities dataset
├── app1.py                         # Preserved: ATS Resume Analyzer (Port 5503)
├── backendreal.py                  # Preserved: Opportunities Tracker (Port 5501)
├── main.py                         # Preserved: FAISS AI Career Chatbot (Port 8000)
├── run_server.py                   # FastAPI application launcher script
├── run-all-backends.bat            # Batch launcher for all 4 microservices
├── sign-in.html                    # AutoHire AI Authentication UI
├── dashboard.html                  # AutoHire AI Main User Dashboard
├── requirements.txt                # Python dependencies
└── .env                            # Application secrets and credentials
```

---

## 🛡️ License & Copyright
AutoHire AI © 2026. All rights reserved.
