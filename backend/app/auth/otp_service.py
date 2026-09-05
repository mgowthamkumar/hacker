import time
import secrets
import logging
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.config import settings
from backend.app.models.otp import OTPRecord
from backend.app.utils.security import generate_secure_otp, hash_otp, timing_safe_compare

logger = logging.getLogger("autohire.otp_service")


def create_otp_challenge(db: Session, email: str) -> Tuple[str, str]:
    """
    Generates a secure 6-digit OTP, salted HMAC hash, and associates it with a unique temp_token.
    Returns (temp_token, raw_otp).
    The raw_otp must only be passed to email_service, never saved to DB or exposed to client.
    """
    raw_otp = generate_secure_otp()
    salt = secrets.token_hex(16)
    hashed = hash_otp(raw_otp, salt)
    temp_token = secrets.token_urlsafe(32)
    now = time.time()
    expires_at = now + settings.OTP_EXPIRY_SECONDS

    otp_record = OTPRecord(
        email=email.strip().lower(),
        temp_token=temp_token,
        hashed_otp=hashed,
        salt=salt,
        expires_at=expires_at,
        attempts=0,
        max_attempts=settings.MAX_OTP_ATTEMPTS,
        resend_count=0,
        last_resend_at=now,
        is_used=False,
        created_at=now
    )
    db.add(otp_record)
    db.commit()

    return temp_token, raw_otp


def verify_otp_challenge(db: Session, temp_token: str, entered_otp: str) -> Tuple[bool, str, Optional[str]]:
    """
    Verifies entered OTP against salted hash.
    Returns (is_valid: bool, status_message: str, user_email: Optional[str]).
    """
    record = db.query(OTPRecord).filter(
        OTPRecord.temp_token == temp_token,
        OTPRecord.is_used == False
    ).first()

    if not record:
        return False, "This verification session has expired. Please sign in again.", None

    now = time.time()

    # 1. Check expiration
    if record.is_expired():
        record.is_used = True
        db.commit()
        return False, "This verification code has expired. Please request a new code.", None

    # 2. Check maximum attempts
    if record.has_exceeded_attempts():
        record.is_used = True
        db.commit()
        return False, "Too many attempts. Please request a new verification code.", None

    # 3. Timing-safe comparison of entered OTP hash
    computed_hash = hash_otp(entered_otp.strip(), record.salt)
    if not timing_safe_compare(computed_hash, record.hashed_otp):
        record.attempts += 1
        if record.attempts >= record.max_attempts:
            record.is_used = True
            db.commit()
            return False, "Too many attempts. Please request a new verification code.", None

        db.commit()
        return False, "Invalid verification code. Please check the code and try again.", None

    # 4. Success -> Mark OTP as used immediately (Single-use policy)
    record.is_used = True
    db.commit()

    return True, "Verification successful.", record.email


def resend_otp_challenge(db: Session, temp_token: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    Regenerates a new 6-digit OTP for the session if cooldown period has elapsed.
    Returns (success: bool, message: str, email: Optional[str], new_otp: Optional[str]).
    """
    record = db.query(OTPRecord).filter(
        OTPRecord.temp_token == temp_token,
        OTPRecord.is_used == False
    ).first()

    if not record:
        return False, "This verification session has expired. Please sign in again.", None, None

    now = time.time()

    # Rate limiting: Enforce cooldown
    elapsed = now - record.last_resend_at
    if elapsed < settings.OTP_COOLDOWN_SECONDS:
        remaining = int(settings.OTP_COOLDOWN_SECONDS - elapsed)
        return False, f"Please wait {remaining} seconds before requesting a new verification code.", None, None

    # Rate limiting: Maximum resends per session
    if record.resend_count >= settings.MAX_RESEND_COUNT:
        record.is_used = True
        db.commit()
        return False, "Maximum resend limit reached for this session. Please start sign-in again.", None, None

    # Generate NEW OTP and salt
    new_otp = generate_secure_otp()
    new_salt = secrets.token_hex(16)
    record.hashed_otp = hash_otp(new_otp, new_salt)
    record.salt = new_salt
    record.expires_at = now + settings.OTP_EXPIRY_SECONDS
    record.attempts = 0
    record.resend_count += 1
    record.last_resend_at = now

    db.commit()

    return True, "A new 6-digit verification code has been generated.", record.email, new_otp
