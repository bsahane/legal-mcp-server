import json
import re
from pathlib import Path
from typing import Optional

from indian_legal_mcp_server.services.statute_index import StatuteIndex
from indian_legal_mcp_server.utils.formatters import (
    format_confidence,
    format_data_freshness,
)
from indian_legal_mcp_server.prompts.system_instructions import DISCLAIMER

FIRST_SCHEDULE_PATH = "indian_legal_mcp_server/data/first_schedule.json"

KEYWORD_BAILABLE = [
    "defamation",
    "public nuisance",
    "simple hurt",
    "assault",
    "criminal trespass",
    "cheating",
    "breach of contract",
    "bribery",
    "forgery",
    "mischief",
    "criminal breach of trust",
]

KEYWORD_NON_BAILABLE = [
    "murder",
    "culpable homicide",
    "rape",
    "dowry death",
    "robbery",
    "dacoity",
    "kidnapping",
    "extortion",
    "terrorist act",
    "sedition",
    "waging war",
    "organized crime",
    "human trafficking",
    "acid attack",
    "attempt to murder",
    "grievous hurt",
    "unnatural offences",
    "abetment of suicide",
    "possession of counterfeit",
]

SECTION_PATTERN = re.compile(
    r"(?:section|sec|s|s\.)\s*(\d+[A-Za-z]*)"
    r"|(?:BNS|bnS|IPC|ipc)\s*(\d+[A-Za-z]*)"
    r"|bns_2023\.s\.(\d+[A-Za-z]*)"
)

FIRST_SCHEDULE: Optional[dict[str, dict]] = None
STATUTE_INDEX: Optional[StatuteIndex] = None


def get_index() -> StatuteIndex:
    global STATUTE_INDEX
    if STATUTE_INDEX is None:
        STATUTE_INDEX = StatuteIndex.from_default_path()
    return STATUTE_INDEX


def load_first_schedule() -> dict[str, dict]:
    global FIRST_SCHEDULE
    if FIRST_SCHEDULE is not None:
        return FIRST_SCHEDULE
    path = Path(FIRST_SCHEDULE_PATH)
    if not path.exists():
        FIRST_SCHEDULE = {}
        return FIRST_SCHEDULE
    with open(path) as f:
        data = json.load(f)
    FIRST_SCHEDULE = {entry["section"]: entry for entry in data}
    return FIRST_SCHEDULE


def extract_section_number(charge: str) -> Optional[str]:
    m = SECTION_PATTERN.search(charge)
    if m:
        return next(g for g in m.groups() if g is not None)
    return None


def classify_charge(charge: str) -> dict:
    section_num = extract_section_number(charge)
    if section_num:
        schedule = load_first_schedule()
        entry = schedule.get(section_num)
        if entry:
            return {
                "charge": charge,
                "section_number": section_num,
                "bailable": entry["bailable"],
                "cognizable": entry["cognizable"],
                "compoundable": entry["compoundable"],
                "trial_by": entry.get("trial_by", ""),
                "punishment": entry.get("punishment", ""),
                "classification_source": "first_schedule",
            }

    cl = charge.lower()
    for nb in KEYWORD_NON_BAILABLE:
        if nb in cl:
            return {
                "charge": charge,
                "section_number": section_num or "unknown",
                "bailable": False,
                "cognizable": True,
                "compoundable": False,
                "trial_by": "Unknown",
                "classification_source": "keyword",
            }
    for b in KEYWORD_BAILABLE:
        if b in cl:
            return {
                "charge": charge,
                "section_number": section_num or "unknown",
                "bailable": True,
                "cognizable": True,
                "compoundable": True,
                "trial_by": "Magistrate First Class",
                "classification_source": "keyword",
            }

    return {
        "charge": charge,
        "section_number": section_num or "unknown",
        "bailable": None,
        "cognizable": None,
        "compoundable": None,
        "trial_by": "Unknown",
        "classification_source": "unrecognized",
    }


def classify_bailability(charges: list[str]) -> dict:
    classified = [classify_charge(c) for c in charges]
    bailable = [c for c in classified if c["bailable"] is True]
    non_bailable = [c for c in classified if c["bailable"] is False]
    unknown = [c for c in classified if c["bailable"] is None]

    return {
        "bailable_charges": bailable,
        "non_bailable_charges": non_bailable,
        "unknown_charges": unknown,
        "has_non_bailable": len(non_bailable) > 0,
        "classifications": classified,
    }


def determine_bail_type(
    classification: dict, investigation_stage: str, is_first_offence: bool
) -> dict:
    if investigation_stage == "pre-arrest":
        primary_type = "anticipatory"
        section = "s. 482 BNSS"
    elif classification["has_non_bailable"]:
        primary_type = "regular_non_bailable"
        section = "s. 483 BNSS"
    else:
        primary_type = "regular_bailable"
        section = "s. 478-479 BNSS"

    if classification["has_non_bailable"] and not is_first_offence:
        likelihood = "low"
    elif classification["has_non_bailable"] and is_first_offence:
        likelihood = "moderate"
    else:
        likelihood = "high"

    return {
        "bail_type": primary_type,
        "governing_section": section,
        "likelihood": likelihood,
    }


async def bail_assessment(
    charges: list[str],
    criminal_history: str = "none",
    is_first_offence: bool = True,
    investigation_stage: str = "pre-arrest",
    max_results: int = 10,
) -> dict:
    try:
        index = get_index()
        classification = classify_bailability(charges)
        bail_type_info = determine_bail_type(
            classification, investigation_stage, is_first_offence
        )

        bail_sections = index.search("BNSS bail section", max_results=max_results)
        relevant_sections = []
        for s in bail_sections:
            relevant_sections.append(
                {
                    "act": s.get("full_title", ""),
                    "section": s["section_number"],
                    "section_title": s["section_title"],
                    "text": s["text"],
                }
            )

        conditions = (
            [
                "Surrender of passport",
                "Regular reporting to police station",
                "Surety bond of appropriate amount",
                "Not to leave jurisdiction without court permission",
                "Not to tamper with evidence or intimidate witnesses",
            ]
            if bail_type_info["likelihood"] in ("moderate", "low")
            else [
                "Personal bond",
                "Surety may be waived for smaller amounts",
            ]
        )

        freshness = format_data_freshness(
            statute_index_built="2026-07-16",
            act_last_verified="2026-07-01",
        )

        return {
            "status": "success",
            "bail_type": bail_type_info["bail_type"],
            "governing_section": bail_type_info["governing_section"],
            "likelihood": bail_type_info["likelihood"],
            "classification": classification,
            "factors": {
                "is_first_offence": is_first_offence,
                "criminal_history": criminal_history,
                "investigation_stage": investigation_stage,
                "total_charges": len(charges),
                "has_non_bailable_charge": classification["has_non_bailable"],
            },
            "likely_conditions": conditions,
            "relevant_sections": relevant_sections[:5],
            "recommendation": (
                "File anticipatory bail application under s. 482 BNSS immediately"
                if investigation_stage == "pre-arrest"
                else "File regular bail application before the concerned court"
            ),
            "confidence": format_confidence(
                0.85 if classification["has_non_bailable"] else 0.9
            ),
            "data_freshness": freshness,
            "disclaimer": DISCLAIMER,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "charges": charges,
        }
