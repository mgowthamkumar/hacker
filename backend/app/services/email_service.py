import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.app.config import settings

logger = logging.getLogger("autohire.email")


def send_otp_email(recipient_email: str, otp_code: str) -> tuple[bool, str]:
    """
    Sends a production OTP verification email via SMTP (Port 465 SSL or 587 STARTTLS).
    Returns (success: bool, message_or_error: str).
    Strictly reports failure if credentials are missing or the SMTP server rejects the message.
    """
    # Check for SMTP credentials
    smtp_user = settings.SMTP_USER
    smtp_pass = settings.SMTP_PASS

    if not smtp_user or not smtp_pass:
        err_msg = "SMTP credentials (SMTP_USER / SMTP_PASS) are not configured in .env."
        logger.warning(f"[EMAIL SERVICE] ❌ Delivery blocked: {err_msg}")
        return False, "Unable to send verification code. Please configure email credentials in .env."

    subject = f"AutoHire AI - Your Verification Code is {otp_code}"
    sender = settings.EMAIL_FROM or f'"AutoHire AI Security" <{smtp_user}>'

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>AutoHire AI Verification Code</title>
</head>
<body style="margin:0; padding:20px; background-color:#0f172a; font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color:#f8fafc;">
    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:540px; background-color:#1e293b; border-radius:16px; overflow:hidden; border:1px solid rgba(255,255,255,0.1); box-shadow:0 20px 40px rgba(0,0,0,0.4);">
        <tr>
            <td style="padding:32px 32px 20px; background:linear-gradient(135deg, rgba(2,132,199,0.2) 0%, rgba(168,85,247,0.2) 100%); border-bottom:1px solid rgba(255,255,255,0.08);">
                <div style="font-size:24px; font-weight:800; color:#ffffff; letter-spacing:-0.02em;">
                    🤖 Auto<span style="color:#38bdf8;">Hire AI</span>
                </div>
                <div style="font-size:13px; color:#94a3b8; margin-top:4px;">Security & Account Verification</div>
            </td>
        </tr>
        <tr>
            <td style="padding:32px;">
                <h2 style="font-size:20px; font-weight:700; color:#ffffff; margin-top:0; margin-bottom:12px;">Verify your email address</h2>
                <p style="color:#cbd5e1; font-size:15px; line-height:1.6; margin-top:0; margin-bottom:24px;">
                    Your verification code is:
                </p>
                <div style="text-align:center; margin:28px 0;">
                    <div style="display:inline-block; padding:16px 36px; background-color:#0f172a; border:2px solid #38bdf8; border-radius:12px; font-size:34px; font-weight:800; letter-spacing:8px; color:#38bdf8; text-shadow:0 0 16px rgba(56,189,248,0.4);">
                        {otp_code}
                    </div>
                </div>
                <div style="background-color:rgba(234,179,8,0.1); border-left:4px solid #eab308; padding:12px 16px; border-radius:6px; font-size:13px; color:#fef08a; line-height:1.5; margin-bottom:24px;">
                    ⏱️ <strong>This code expires in 5 minutes.</strong> Do not share this code with anyone.
                </div>
                <hr style="border:none; border-top:1px solid rgba(255,255,255,0.1); margin:24px 0 16px;">
                <p style="font-size:12px; color:#94a3b8; margin:0; line-height:1.5;">
                    If you did not request this code, you can ignore this email. Someone may have entered your email address by mistake.
                </p>
            </td>
        </tr>
        <tr>
            <td style="padding:16px 32px; background-color:#0f172a; border-top:1px solid rgba(255,255,255,0.05); text-align:center; font-size:12px; color:#64748b;">
                &copy; AutoHire AI Security Engine &middot; All rights reserved.
            </td>
        </tr>
    </table>
</body>
</html>"""

    plain_text = f"""AutoHire AI
Your verification code is: {otp_code}

This code expires in 5 minutes.
If you did not request this code, you can ignore this email."""

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient_email
    message["X-Priority"] = "1"
    message["Importance"] = "high"

    message.attach(MIMEText(plain_text, "plain", "utf-8"))
    message.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        host = settings.SMTP_HOST or "smtp.gmail.com"
        port = settings.SMTP_PORT or 465

        # Port 465 uses SSL directly (Standard for Gmail SSL)
        if port == 465 or settings.SMTP_SECURE:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=12) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, recipient_email, message.as_string())
        else:
            # Port 587 uses STARTTLS
            with smtplib.SMTP(host, port, timeout=12) as server:
                server.ehlo()
                context = ssl.create_default_context()
                server.starttls(context=context)
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, recipient_email, message.as_string())

        logger.info(f"[EMAIL SERVICE] ✅ Real OTP dispatched successfully to {recipient_email}")
        return True, "Verification code sent to your email inbox."

    except smtplib.SMTPAuthenticationError as auth_err:
        logger.error(f"[EMAIL SERVICE] ❌ SMTP Authentication Failed: {auth_err}")
        return False, "Unable to send verification code. SMTP authentication failed. Please verify your Google App Password."

    except (smtplib.SMTPException, OSError) as e:
        logger.error(f"[EMAIL SERVICE] ❌ SMTP Delivery Error: {e}")
        return False, f"Unable to send verification code. Delivery error: {str(e)}"
