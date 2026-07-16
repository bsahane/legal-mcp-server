from datetime import date, datetime, timedelta
from typing import Optional

from indian_legal_mcp_server.utils.formatters import format_confidence
from indian_legal_mcp_server.prompts.system_instructions import DISCLAIMER

LIMITATION_PERIODS = {
    "contract_written": {
        "period_years": 3,
        "section": "Schedule I, Art. 1-55",
        "description": "Contracts in writing",
    },
    "contract_oral": {
        "period_years": 3,
        "section": "Schedule I, Art. 56-63",
        "description": "Oral contracts",
    },
    "debt_recovery": {
        "period_years": 3,
        "section": "Schedule I, Art. 1-7",
        "description": "Debt / money recovery",
    },
    "promissory_note": {
        "period_years": 3,
        "section": "Schedule I, Art. 28-37",
        "description": "Promissory note / bills of exchange",
    },
    "property_possession": {
        "period_years": 12,
        "section": "s. 65, Schedule I, Art. 64-67",
        "description": "Recovery of immovable property",
    },
    "property_title": {
        "period_years": 12,
        "section": "s. 65, Schedule I, Art. 64-67",
        "description": "Declaration of title / ownership",
    },
    "easement": {
        "period_years": 20,
        "section": "s. 25-26",
        "description": "Acquisition of easement / prescription",
    },
    "tort_damages": {
        "period_years": 1,
        "section": "Schedule I, Art. 68-76",
        "description": "Torts — damages for wrongs",
    },
    "defamation": {
        "period_years": 1,
        "section": "Schedule I, Art. 75",
        "description": "Defamation / libel / slander",
    },
    "malicious_prosecution": {
        "period_years": 1,
        "section": "Schedule I, Art. 74",
        "description": "Malicious prosecution",
    },
    "fraud": {
        "period_years": 3,
        "section": "s. 17",
        "description": "Fraud — time runs from discovery",
    },
    "mistake": {
        "period_years": 3,
        "section": "s. 17",
        "description": "Mistake — time runs from discovery",
    },
    "trust_breach": {
        "period_years": 3,
        "section": "s. 10",
        "description": "Breach of trust — no limitation for express trusts",
    },
    "government_suit": {
        "period_years": 30,
        "section": "s. 32",
        "description": "Suits by or against government",
    },
    "consumer_complaint": {
        "period_years": 2,
        "section": "CPA 2019 s. 69",
        "description": "Consumer complaint — from date of cause of action",
    },
    "cheque_bounce": {
        "period_years": 1,
        "section": "NI Act s. 142",
        "description": "Cheque bounce — from date of dishonour",
    },
    "arbitration": {
        "period_years": 3,
        "section": "Schedule I, Art. 1",
        "description": "Arbitration — from date of dispute arising",
    },
    "criminal_law": {
        "period_years": None,
        "section": "BNS/BNSS",
        "description": "No limitation for serious crimes (murder, rape); cognizance bars apply under BNSS",
    },
    "maintenance": {
        "period_years": 1,
        "section": "BNSS s. 144",
        "description": "Maintenance claim — from date of refusal",
    },
    "divorce": {
        "period_years": 1,
        "section": "HMA s. 14",
        "description": "Divorce — petition not entertainable within 1 year of marriage",
    },
}

SUIT_TYPES_BY_KEYWORD = {
    "debt": "debt_recovery",
    "loan": "debt_recovery",
    "recovery": "debt_recovery",
    "contract": "contract_written",
    "agreement": "contract_written",
    "promissory": "promissory_note",
    "note": "promissory_note",
    "property": "property_possession",
    "land": "property_possession",
    "possession": "property_possession",
    "title": "property_title",
    "ownership": "property_title",
    "easement": "easement",
    "prescription": "easement",
    "tort": "tort_damages",
    "damage": "tort_damages",
    "injury": "tort_damages",
    "defamation": "defamation",
    "libel": "defamation",
    "slander": "defamation",
    "malicious": "malicious_prosecution",
    "prosecution": "malicious_prosecution",
    "fraud": "fraud",
    "cheat": "fraud",
    "mistake": "mistake",
    "trust": "trust_breach",
    "government": "government_suit",
    "consumer": "consumer_complaint",
    "defective": "consumer_complaint",
    "cheque": "cheque_bounce",
    "dishonour": "cheque_bounce",
    "138": "cheque_bounce",
    "arbitration": "arbitration",
    "criminal": "criminal_law",
    "crime": "criminal_law",
    "maintenance": "maintenance",
    "alimony": "maintenance",
    "divorce": "divorce",
    "dissolution": "divorce",
}


def calculate_expiry(cause_of_action_date: date, period_years: int) -> date:
    try:
        return cause_of_action_date.replace(
            year=cause_of_action_date.year + period_years
        )
    except ValueError:
        return cause_of_action_date + timedelta(days=365 * period_years)


def suggest_suit_type(cause_description: str) -> str:
    cd = cause_description.lower()
    for keyword, suit_type in SUIT_TYPES_BY_KEYWORD.items():
        if keyword in cd:
            return suit_type
    return "contract_written"


async def limitation_calculator(
    cause_description: str,
    cause_of_action_date: str,
    suit_type: Optional[str] = None,
) -> dict:
    try:
        cause_date = date.fromisoformat(cause_of_action_date)
    except ValueError:
        return {
            "status": "error",
            "error": "Invalid date format. Use YYYY-MM-DD (e.g., 2024-01-15).",
        }

    if not suit_type:
        suit_type = suggest_suit_type(cause_description)

    period_info = LIMITATION_PERIODS.get(suit_type)
    if not period_info:
        return {
            "status": "error",
            "error": f"Unknown suit type '{suit_type}'. Valid types: {', '.join(sorted(LIMITATION_PERIODS.keys()))}",
        }

    today = date.today()
    if period_info["period_years"] is None:
        expiry_date = None
        days_remaining = None
        status = "no_limitation"
        status_text = "No fixed limitation period (criminal law varies by offence)"
    else:
        expiry_date = calculate_expiry(cause_date, period_info["period_years"])
        days_remaining = (expiry_date - today).days
        if days_remaining < 0:
            status = "expired"
            status_text = (
                f"LIMITATION EXPIRED {abs(days_remaining)} days ago on {expiry_date}"
            )
        elif days_remaining == 0:
            status = "expires_today"
            status_text = "LIMITATION EXPIRES TODAY — file immediately"
        elif days_remaining <= 30:
            status = "critical"
            status_text = (
                f"URGENT: Only {days_remaining} days remaining — file immediately"
            )
        elif days_remaining <= 90:
            status = "warning"
            status_text = f"Warning: {days_remaining} days remaining — file soon"
        else:
            status = "safe"
            status_text = f"{days_remaining} days remaining — within limitation period"

    return {
        "status": "success",
        "suit_type": suit_type,
        "description": period_info["description"],
        "cause_of_action_date": cause_of_action_date,
        "limitation_period_years": period_info["period_years"],
        "governing_provision": period_info["section"],
        "expiry_date": str(expiry_date) if expiry_date else "N/A (no fixed period)",
        "days_remaining": days_remaining,
        "limitation_status": status,
        "status_text": status_text,
        "extension_possible": {
            "fraud_or_mistake": suit_type in ("fraud", "mistake"),
            "legal_disability": True,
            "acknowledgement": True,
            "part_payment": True,
        },
        "disclaimer": DISCLAIMER,
        "confidence": format_confidence(0.95),
    }
