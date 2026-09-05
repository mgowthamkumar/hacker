import os
import json
import smtplib
import ssl
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from backend.app.config import settings, BASE_DIR
from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.schemas.auth import (
    GoogleAuthRequest,
    VerifyOtpRequest,
    ResendOtpRequest,
    LoginRequest,
    RegisterRequest,
    ConfigureSmtpRequest
)
from backend.app.auth.google_oauth import verify_google_id_token
from backend.app.auth.otp_service import create_otp_challenge, verify_otp_challenge, resend_otp_challenge
from backend.app.auth.session import set_session_cookie, clear_session_cookie, get_current_user_optional
from backend.app.services.email_service import send_otp_email
from backend.app.utils.security import mask_email, hash_password, generate_salt, verify_password

router = APIRouter(tags=["Authentication"])


def sync_users_json(db: Session):
    """Synchronizes users to users.json for backward compatibility."""
    users = db.query(User).all()
    out = []
    for u in users:
        out.append({
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "passwordSalt": u.password_salt,
            "passwordHash": u.password_hash,
            "isVerified": u.is_verified,
            "emailVerified": u.email_verified,
            "verifiedAt": u.verified_at.isoformat() if u.verified_at else None,
            "profile": json.loads(u.profile_data) if u.profile_data else {
                "fullName": u.name,
                "emailAddress": u.email,
                "picture": u.picture
            }
        })
    try:
        with open(BASE_DIR / "users.json", "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
    except Exception as e:
        print(f"Notice syncing users.json: {e}")


@router.post("/api/auth/google")
@router.post("/auth/google")
async def google_auth(req: GoogleAuthRequest, response: Response, db: Session = Depends(get_db)):
    try:
        profile = await verify_google_id_token(req.credential)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Google authentication failed: {str(e)}")

    email = profile["email"]
    name = profile.get("name") or email.split("@")[0]
    picture = profile.get("picture", "")

    # Retrieve or create user record
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            id=profile.get("sub") or f"user_{int(datetime.utcnow().timestamp())}",
            email=email,
            name=name,
            picture=picture,
            is_verified=False,
            email_verified=False,
            profile_data=json.dumps({
                "fullName": name,
                "emailAddress": email,
                "picture": picture
            })
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Subsequent Login Check: If account was verified via OTP, SKIP OTP COMPLETELY!
    if user.is_verified or user.email_verified:
        if picture and not user.picture:
            user.picture = picture
            db.commit()

        set_session_cookie(response, user.id)
        return {
            "success": True,
            "pendingOtp": False,
            "alreadyVerified": True,
            "message": "Welcome back! Account verified.",
            "redirect": "dashboard.html",
            "user": user.to_dict()
        }

    # First-Time Sign-In: Generate secure 6-digit OTP on backend
    temp_token, raw_otp = create_otp_challenge(db, email)

    # Real Email Delivery via SMTP
    email_sent, email_msg = send_otp_email(email, raw_otp)
    if not email_sent:
        # Failure handling: Strictly notify user that code could not be sent
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send verification code. Please try again."
        )

    # Only show OTP verification screen when email delivery succeeds
    return {
        "success": True,
        "pendingOtp": True,
        "tempToken": temp_token,
        "email": mask_email(email)
    }


@router.post("/api/auth/verify-otp")
@router.post("/auth/verify-otp")
def verify_otp(req: VerifyOtpRequest, response: Response, db: Session = Depends(get_db)):
    is_valid, msg, email = verify_otp_challenge(db, req.tempToken, req.otp)
    if not is_valid:
        raise HTTPException(status_code=400, detail=msg)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    # Mark as verified
    user.is_verified = True
    user.email_verified = True
    user.verified_at = datetime.utcnow()
    db.commit()

    # Synchronize users.json
    sync_users_json(db)

    # Issue session cookie
    set_session_cookie(response, user.id)

    return {
        "success": True,
        "message": "Authentication successful.",
        "redirect": "dashboard.html",
        "user": user.to_dict()
    }


@router.post("/api/auth/resend-otp")
@router.post("/auth/resend-otp")
def resend_otp(req: ResendOtpRequest, db: Session = Depends(get_db)):
    success, msg, email, new_otp = resend_otp_challenge(db, req.tempToken)
    if not success:
        # Rate limiting or limit exceeded
        raise HTTPException(status_code=429 if "wait" in msg.lower() else 400, detail=msg)

    # Send new OTP
    email_sent, email_msg = send_otp_email(email, new_otp)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send verification code. Please try again."
        )

    return {
        "success": True,
        "message": "A new 6-digit verification code has been dispatched to your email.",
        "email": mask_email(email)
    }


@router.post("/api/auth/logout")
@router.post("/auth/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"success": True, "message": "Logged out successfully."}


@router.get("/api/auth/me")
@router.get("/auth/me")
def get_me(user: Optional[User] = Depends(get_current_user_optional)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    return {"user": user.to_dict()}


@router.post("/api/auth/login")
@router.post("/auth/login")
def password_login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if not verify_password(req.password, user.password_salt, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    set_session_cookie(response, user.id)
    return {
        "success": True,
        "message": "Logged in successfully.",
        "redirect": "dashboard.html",
        "user": user.to_dict()
    }


@router.post("/api/auth/register")
@router.post("/auth/register")
def password_register(req: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    salt = generate_salt()
    pw_hash = hash_password(req.password, salt)
    name = req.name.strip() if req.name else email.split("@")[0]
    user_id = f"user_{int(datetime.utcnow().timestamp())}"

    user = User(
        id=user_id,
        email=email,
        name=name,
        password_hash=pw_hash,
        password_salt=salt,
        is_verified=True,
        email_verified=True,
        verified_at=datetime.utcnow(),
        profile_data=json.dumps({"fullName": name, "emailAddress": email})
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    sync_users_json(db)
    set_session_cookie(response, user.id)

    return {
        "success": True,
        "message": "Account created successfully.",
        "redirect": "dashboard.html",
        "user": user.to_dict()
    }


@router.get("/api/auth/smtp-status")
@router.get("/auth/smtp-status")
def get_smtp_status():
    has_creds = bool(settings.SMTP_USER and settings.SMTP_PASS)
    return {
        "configured": has_creds,
        "smtpUser": settings.SMTP_USER or "mgowthamkumar472008@gmail.com",
        "mode": "gmail_ssl" if has_creds else "unconfigured"
    }


@router.post("/api/auth/configure-smtp")
@router.post("/auth/configure-smtp")
def configure_smtp(req: ConfigureSmtpRequest):
    app_password = (req.appPassword or req.password or "").replace(" ", "").strip()
    smtp_user = (req.email or settings.SMTP_USER or "mgowthamkumar472008@gmail.com").strip()

    if not app_password or len(app_password) < 8:
        raise HTTPException(status_code=400, detail="Please provide a valid 16-character Google App Password.")

    # Test SMTP connection with Google
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=10) as server:
            server.login(smtp_user, app_password)
    except smtplib.SMTPAuthenticationError as auth_err:
        raise HTTPException(
            status_code=400,
            detail=f"Google rejected this App Password: {str(auth_err)}. Please generate an App Password at myaccount.google.com/apppasswords."
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")

    # Update .env file
    env_path = BASE_DIR / ".env"
    content = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    if "SMTP_PASS=" in content:
        content = "\n".join([f"SMTP_PASS={app_password}" if line.startswith("SMTP_PASS=") else line for line in content.splitlines()])
    else:
        content += f"\nSMTP_PASS={app_password}\n"

    if "SMTP_USER=" in content:
        content = "\n".join([f"SMTP_USER={smtp_user}" if line.startswith("SMTP_USER=") else line for line in content.splitlines()])
    else:
        content += f"\nSMTP_USER={smtp_user}\n"

    env_path.write_text(content, encoding="utf-8")
    settings.SMTP_PASS = app_password
    settings.SMTP_USER = smtp_user

    return {
        "success": True,
        "message": f"Google authenticated successfully! Real Gmail OTP delivery is now active for {smtp_user}."
    }
