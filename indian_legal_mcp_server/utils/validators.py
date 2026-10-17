import re

from pydantic import BaseModel, field_validator

INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"disregard\s+(the\s+)?system\s+prompt",
    r"system\s+prompt:",
]

CNR_PATTERN = re.compile(r"^[A-Z]{4}\d{2}-\d{6}-\d{4}$")


class ScenarioInput(BaseModel):
    scenario: str

    @field_validator("scenario")
    def validate_scenario(cls, v):
        if len(v) < 10:
            raise ValueError(
                "Scenario too short — provide more detail for accurate analysis"
            )
        if len(v) > 10000:
            raise ValueError("Scenario too long — maximum 10,000 characters")
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid input detected")
        return v


class CNRInput(BaseModel):
    cnr_number: str

    @field_validator("cnr_number")
    def validate_cnr(cls, v):
        v = v.strip().upper()
        if not CNR_PATTERN.match(v):
            raise ValueError("Invalid CNR format. Expected: XXHC01-123456-2024")
        return v


def validate_date(date_str: str) -> bool:
    try:
        from datetime import date

        parts = date_str.split("-")
        if len(parts) != 3:
            return False
        date(int(parts[0]), int(parts[1]), int(parts[2]))
        return True
    except (ValueError, IndexError):
        return False


def validate_section_ref(ref: str) -> bool:
    return bool(re.match(r"^[a-z_0-9]+\.s\.[0-9A-Za-z()]+$", ref))
