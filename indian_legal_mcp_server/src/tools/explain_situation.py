"""
Scenario Explanation Tool.

Takes a free-text legal scenario and returns plain-language explanation,
applicable law, rights, and next steps.
"""

from indian_legal_mcp_server.prompts.explain_situation_prompt import (
    build_explain_situation_prompt,
)
from indian_legal_mcp_server.prompts.system_instructions import DISCLAIMER
from indian_legal_mcp_server.services.citation_validator import (
    expand_citations,
    validate_citations,
)
from indian_legal_mcp_server.services.llm_client import get_llm_client
from indian_legal_mcp_server.src.settings import settings
from indian_legal_mcp_server.src.tools._impl.statute_search import statute_search
from indian_legal_mcp_server.utils.formatters import (
    format_confidence,
    format_data_freshness,
)
from indian_legal_mcp_server.utils.privacy import hash_scenario, redact_pii
from indian_legal_mcp_server.utils.validators import ScenarioInput

CLASSIFICATION_RULES = {
    "arrest_and_bail": {
        "keywords": [
            "arrested",
            "FIR",
            "police station",
            "bail",
            "custody",
            "remand",
            "arrest",
            "detention",
            "jail",
        ],
        "domain": "criminal",
    },
    "maintenance": {
        "keywords": ["maintenance", "alimony", "wife maintenance", "child support"],
        "domain": "family",
    },
    "cheque_bounce": {
        "keywords": ["cheque bounce", "dishonour", "138", "NI Act", "check bounce"],
        "domain": "commercial",
    },
    "domestic_violence": {
        "keywords": [
            "domestic violence",
            "DV act",
            "dowry",
            "beat",
            "harassment",
            "torture",
        ],
        "domain": "family",
    },
    "divorce": {
        "keywords": ["divorce", "mutual consent", "separation", "talaq", "cruelty"],
        "domain": "family",
    },
    "property_dispute": {
        "keywords": ["property", "land", "ownership", "inheritance", "succession"],
        "domain": "civil",
    },
    "consumer_complaint": {
        "keywords": ["consumer", "defective", "deficiency", "service", "product"],
        "domain": "commercial",
    },
    "cyber_crime": {
        "keywords": [
            "cyber",
            "online",
            "hacking",
            "phishing",
            "data theft",
            "computer",
        ],
        "domain": "criminal",
    },
}


def classify_scenario(scenario: str) -> dict:
    scenario_lower = scenario.lower()
    best_match = None
    best_score = 0

    for category, config in CLASSIFICATION_RULES.items():
        score = sum(1 for kw in config["keywords"] if kw in scenario_lower)
        if score > best_score:
            best_score = score
            best_match = category

    if best_match and best_score > 0:
        return {
            "primary_domain": CLASSIFICATION_RULES[best_match]["domain"],
            "sub_domain": best_match,
            "confidence": min(0.5 + best_score * 0.1, 0.95),
        }

    return {
        "primary_domain": "unknown",
        "sub_domain": "general",
        "confidence": 0.3,
    }


async def explain_situation(
    scenario: str,
    detail_level: str = "standard",
    include_checklist: bool = True,
) -> dict:
    try:
        scenario_hash = hash_scenario(scenario)
        redacted = redact_pii(scenario) if settings.REDACT_SCENARIO_INPUT else scenario

        ScenarioInput(scenario=scenario)

        classification = classify_scenario(scenario)

        search_results = await statute_search(
            query=scenario,
            max_results=5,
        )

        indexed_sections = set()
        if search_results.get("status") == "success":
            for s in search_results.get("sections", []):
                indexed_sections.add(f"{s['act_id']}.s.{s['section']}")

        llm = get_llm_client()

        if settings.ENABLE_LLM_TOOLS:
            prompt = build_explain_situation_prompt(
                scenario, search_results.get("sections", []), classification
            )
            llm_response = await llm.generate(
                system_prompt="You are a legal triage assistant for Indian law. Respond in JSON format as specified.",
                user_prompt=prompt,
                temperature=0.2,
            )
            validated = validate_citations(llm_response, indexed_sections)
            cleaned = validated["cleaned_text"]
            expanded = expand_citations(cleaned)
        else:
            expanded = "LLM tools are disabled. Set ENABLE_LLM_TOOLS=True in .env to enable AI-powered explanations."

        return {
            "status": "success",
            "classification": classification,
            "explanation": expanded,
            "applicable_law": [
                {
                    "provision": f"{s['act_id']}.s.{s['section']}",
                    "relevance": s.get("section_title", ""),
                }
                for s in search_results.get("sections", [])[:5]
            ],
            "your_rights": [],
            "immediate_steps": [],
            "checklist": [f"Consult an advocate regarding {s['act_id']}"]
            if search_results.get("sections")
            else [],
            "caution_points": [],
            "sources_used": ["statute_search"]
            if search_results.get("sections")
            else [],
            "sources_failed": [],
            "disclaimer": DISCLAIMER,
            "data_freshness": search_results.get(
                "data_freshness", format_data_freshness()
            ),
            "confidence": format_confidence(classification.get("confidence", 0.5)),
        }

    except ValueError as e:
        return {
            "status": "error",
            "error": str(e),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"An unexpected error occurred: {str(e)}",
            "scenario_hash": scenario_hash,
        }
