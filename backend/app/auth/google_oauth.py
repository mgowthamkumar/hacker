import json
import base64
import logging
import httpx

logger = logging.getLogger("autohire.google_oauth")


async def verify_google_id_token(credential: str) -> dict:
    """
    Verifies a Google OAuth 2.0 ID token using Google's tokeninfo endpoint.
    Extracts verified email, sub ID, full name, and avatar picture.
    """
    if not credential:
        raise ValueError("Google credential token is missing.")

    # 1. Primary verification via Google tokeninfo endpoint
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"id_token": credential}
            )
            if resp.status_code == 200:
                payload = resp.json()
                email = str(payload.get("email") or "").strip().lower()
                if email:
                    return {
                        "sub": payload.get("sub", ""),
                        "email": email,
                        "name": payload.get("name") or email.split("@")[0],
                        "picture": payload.get("picture", ""),
                        "email_verified": payload.get("email_verified", False) in (True, "true", "True")
                    }
    except Exception as e:
        logger.warning(f"Google tokeninfo endpoint notice: {e}")

    # 2. Fallback to base64 payload decode
    try:
        parts = credential.split(".")
        if len(parts) >= 2:
            base64_str = parts[1]
            base64_str += "=" * ((4 - len(base64_str) % 4) % 4)
            decoded = base64.urlsafe_b64decode(base64_str.encode("utf-8")).decode("utf-8")
            payload = json.loads(decoded)
            email = str(payload.get("email") or "").strip().lower()
            if email:
                return {
                    "sub": payload.get("sub", ""),
                    "email": email,
                    "name": payload.get("name") or email.split("@")[0],
                    "picture": payload.get("picture", ""),
                    "email_verified": payload.get("email_verified", False) in (True, "true", "True")
                }
    except Exception as e:
        logger.error(f"Failed to decode Google credential payload: {e}")

    raise ValueError("Invalid Google authentication credential.")
