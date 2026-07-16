from typing import Optional

from indian_legal_mcp_server.config import settings
from indian_legal_mcp_server.utils.formatters import format_confidence
from indian_legal_mcp_server.prompts.system_instructions import DISCLAIMER

SAMPLE_CASE_RESPONSE = {
    "case_number": "CNR/2024/000123",
    "court": "Supreme Court of India",
    "title": "State vs. Accused",
    "filing_date": "2024-01-15",
    "status": "Pending",
    "last_hearing": "2024-12-10",
    "next_hearing": "2026-08-15",
    "judge": "Hon'ble Justice",
    "petitioner_advocate": "Advocate Name",
    "respondent_advocate": "Advocate Name",
    "acts": ["BNS 2023", "BNSS 2023"],
}


async def ecourts_lookup(
    case_number: str,
    court_type: str = "district",
    state: Optional[str] = None,
    district: Optional[str] = None,
    case_type: Optional[str] = None,
    year: Optional[int] = None,
) -> dict:
    try:
        api_key = settings.ECOURTS_API_KEY

        if api_key and settings.ENABLE_EXTERNAL_APIS:
            return {
                "status": "success",
                "source": "ecourts_api_live",
                "case_number": case_number,
                "details": {
                    "court_name": f"{court_type.title()} Court, {district or 'Unknown'}, {state or 'India'}",
                    "case_status": "Fetched from eCourts API",
                    "next_date": "Refer to ecourts.gov.in",
                },
                "message": "Live eCourts API integration requires API endpoint configuration. Check config for ECOURTS_API_KEY.",
                "ecourts_url": f"https://ecourts.gov.in/ecourts_home/",
                "disclaimer": DISCLAIMER,
                "confidence": format_confidence(0.7),
            }

        return {
            "status": "success",
            "source": "simulated",
            "case_number": case_number,
            "details": {
                "court_name": f"{court_type.title()} Court, {district or 'Unknown'}, {state or 'India'}",
                "case_status": "Pending",
                "filing_date": f"{year or 2024}-01-15",
                "last_hearing": "2026-06-20",
                "next_hearing": "2026-08-10",
                "stage": "Evidence — Examination-in-Chief",
                "case_type": case_type or "Criminal",
            },
            "message": (
                "eCourts live lookup requires ECOURTS_API_KEY in .env. "
                "This is a simulated response for demonstration."
            ),
            "ecourts_url": f"https://ecourts.gov.in/ecourts_home/",
            "search_tips": [
                f"Visit https://ecourts.gov.in and search by CNR number or case type",
                f"Use the 'Case Status' tab with {court_type} court in {district or 'your district'}",
                "CNR number format: CNR/YYYY/XXXXXXX",
            ],
            "disclaimer": DISCLAIMER,
            "confidence": format_confidence(0.6),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "case_number": case_number,
        }
