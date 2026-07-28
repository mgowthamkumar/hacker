import re
from typing import Tuple


def _extract_name_from_resume(raw_text: str) -> str:
    if not raw_text:
        return ""

    patterns = [
        r"\bname\b\s*[:\-]\s*([A-Za-z .'-]+)",
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()

    return ""


def _extract_dob_from_resume(raw_text: str) -> str:
    if not raw_text:
        return ""

    patterns = [
        r"\bdate\s+of\s+birth\b\s*[:\-]\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|[A-Za-z]+ \d{1,2}, \d{4})",
        r"\bdob\b\s*[:\-]\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|[A-Za-z]+ \d{1,2}, \d{4})",
    ]

    for pattern in patterns:
        match = re.search(pattern, raw_text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()

    return ""


def resolve_profile_identity(resume_text: str, submitted_full_name: str, submitted_dob: str) -> Tuple[str, str]:
    detected_name = _extract_name_from_resume(resume_text)
    detected_dob = _extract_dob_from_resume(resume_text)

    full_name = submitted_full_name.strip() if submitted_full_name and submitted_full_name.strip() else detected_name
    dob = submitted_dob.strip() if submitted_dob and submitted_dob.strip() else detected_dob

    return full_name, dob
