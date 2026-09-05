import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded from workspace root
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


class Settings:
    PROJECT_NAME: str = "AutoHire AI Backend"
    VERSION: str = "2.0.0"

    # Server Settings
    PORT: int = int(os.getenv("PORT", "8800"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "autohire-ai-super-secret-key-2026-production")
    SESSION_COOKIE_NAME: str = "autohire_session"
    SESSION_MAX_AGE_DAYS: int = 30

    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")

    # SMTP / Real Email Delivery Settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SMTP_USER: str = os.getenv("SMTP_USER", os.getenv("SMTP_USERNAME", os.getenv("EMAIL_USER", "mgowthamkumar472008@gmail.com"))).strip()
    SMTP_PASS: str = os.getenv("SMTP_PASS", os.getenv("SMTP_PASSWORD", os.getenv("EMAIL_PASS", ""))).replace(" ", "").strip()
    SMTP_SERVICE: str = os.getenv("SMTP_SERVICE", "gmail").lower()
    SMTP_SECURE: bool = os.getenv("SMTP_SECURE", "true").lower() in ("true", "1", "yes")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", os.getenv("SMTP_FROM", f'"AutoHire AI Security" <{SMTP_USER}>'))

    # OTP Security Policy
    OTP_EXPIRY_SECONDS: int = int(os.getenv("OTP_EXPIRY_SECONDS", "300"))  # 5 minutes
    OTP_COOLDOWN_SECONDS: int = int(os.getenv("OTP_COOLDOWN_SECONDS", "45"))  # 45 seconds cooldown
    MAX_OTP_ATTEMPTS: int = int(os.getenv("MAX_OTP_ATTEMPTS", "5"))
    MAX_RESEND_COUNT: int = int(os.getenv("MAX_RESEND_COUNT", "4"))

    # Database Path
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'autohire.db'}")

    # CORS Allowed Origins
    CORS_ORIGINS: list = [
        "http://localhost:8800",
        "http://127.0.0.1:8800",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
        "http://localhost:5503",
        "http://127.0.0.1:5503",
        "https://mgowthamkumar.github.io",
        "https://hacker-drab-mu.vercel.app"
    ]


settings = Settings()
