from typing import Optional

from indian_legal_mcp_server.src.tools.ecourts_lookup import ecourts_lookup


async def legal_lookup(
    source: str,
    case_number: Optional[str] = None,
    court_type: str = "district",
    state: Optional[str] = None,
    district: Optional[str] = None,
    case_type: Optional[str] = None,
    year: Optional[int] = None,
) -> dict:
    if source == "ecourts":
        return await ecourts_lookup(
            case_number=case_number or "",
            court_type=court_type,
            state=state,
            district=district,
            case_type=case_type,
            year=year,
        )
    else:
        return {
            "status": "error",
            "error": f"Unknown lookup source '{source}'. Supported sources: ecourts",
        }
