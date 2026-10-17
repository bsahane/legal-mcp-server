import hashlib
import re

PII_PATTERNS = [
    (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[AADHAAR_MASKED]"),
    (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[PAN_MASKED]"),
    (r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b", "[PHONE_MASKED]"),
    (r"\bFIR\s*No\.?\s*\d+/\d{4}\b", "[FIR_MASKED]"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_MASKED]"),
    (r"\b[A-Z]{4}\d{2}-\d{6}-\d{4}\b", "[CNR_MASKED]"),
]


def redact_pii(text: str) -> str:
    for pattern, replacement in PII_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


def hash_scenario(scenario: str) -> str:
    return hashlib.sha256(scenario.encode()).hexdigest()[:12]


def should_redact() -> bool:
    from indian_legal_mcp_server.src.settings import settings

    return settings.REDACT_SCENARIO_INPUT
