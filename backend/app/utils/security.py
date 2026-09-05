import hmac
import hashlib
import secrets


def generate_salt(length: int = 16) -> str:
    """Generates a secure random hex salt."""
    return secrets.token_hex(length)


def hash_password(password: str, salt: str) -> str:
    """Hashes a password with salt using SHA-512."""
    return hashlib.sha512((password + salt).encode("utf-8")).hexdigest()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Compares candidate password hash against stored hash in constant time."""
    candidate_hash = hash_password(password, salt)
    return hmac.compare_digest(candidate_hash, expected_hash)


def generate_secure_otp() -> str:
    """Generates a cryptographically secure 6-digit OTP."""
    code = secrets.randbelow(900000) + 100000
    return str(code)


def hash_otp(otp: str, salt: str) -> str:
    """Computes HMAC-SHA256 of the OTP using salt as key."""
    return hmac.new(salt.encode("utf-8"), otp.encode("utf-8"), hashlib.sha256).hexdigest()


def timing_safe_compare(a: str, b: str) -> bool:
    """Constant time string comparison to prevent timing attacks."""
    return hmac.compare_digest(a, b)


def mask_email(email: str) -> str:
    """Masks an email for safe display (e.g. m***8@gmail.com)."""
    if not email or "@" not in email:
        return "***@***.com"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        return f"{user[0] if user else '*'}***@{domain}"
    return f"{user[0]}***{user[-1]}@{domain}"
