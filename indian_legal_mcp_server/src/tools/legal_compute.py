from typing import Optional

from indian_legal_mcp_server.src.tools.bail_assessment import bail_assessment
from indian_legal_mcp_server.src.tools.limitation_calculator import (
    limitation_calculator,
)


async def legal_compute(
    compute: str,
    charges: Optional[list[str]] = None,
    criminal_history: str = "none",
    is_first_offence: bool = True,
    investigation_stage: str = "pre-arrest",
    cause_description: Optional[str] = None,
    cause_of_action_date: Optional[str] = None,
    suit_type: Optional[str] = None,
    max_results: int = 10,
) -> dict:
    if compute == "bail":
        return await bail_assessment(
            charges=charges or [],
            criminal_history=criminal_history,
            is_first_offence=is_first_offence,
            investigation_stage=investigation_stage,
            max_results=max_results,
        )
    elif compute == "limitation":
        return await limitation_calculator(
            cause_description=cause_description or "",
            cause_of_action_date=cause_of_action_date or "",
            suit_type=suit_type,
        )
    else:
        return {
            "status": "error",
            "error": f"Unknown compute type '{compute}'. Supported types: bail, limitation",
        }
