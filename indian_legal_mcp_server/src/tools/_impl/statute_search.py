"""
Statute & Section Lookup Tool.

Searches indexed Indian statutes by query text or section number.
Returns verbatim text, section references, and relevance scores.
"""

from typing import Optional
from indian_legal_mcp_server.services.statute_index import StatuteIndex
from indian_legal_mcp_server.services.section_mapper import SectionMapper
from indian_legal_mcp_server.utils.formatters import (
    format_confidence,
    format_data_freshness,
)

MAPPING_PATH = "indian_legal_mcp_server/data/old_to_new_mapping.json"

ACT_TO_OLD_ACT = {
    "bns_2023": "ipc_1860",
    "bnss_2023": "crpc_1973",
}

STATUTE_INDEX: Optional[StatuteIndex] = None
SECTION_MAPPER: Optional[SectionMapper] = None


def get_index() -> StatuteIndex:
    global STATUTE_INDEX
    if STATUTE_INDEX is None:
        STATUTE_INDEX = StatuteIndex.from_default_path()
    return STATUTE_INDEX


def get_mapper() -> SectionMapper:
    global SECTION_MAPPER
    if SECTION_MAPPER is None:
        SECTION_MAPPER = SectionMapper(MAPPING_PATH)
    return SECTION_MAPPER


async def statute_search(
    query: str,
    act_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    include_old_new_mapping: bool = True,
    max_results: int = 10,
) -> dict:
    try:
        index = get_index()
        results = index.search(query, act_filter=act_filter, max_results=max_results)
        mapper = get_mapper() if include_old_new_mapping else None

        if category_filter:
            results = [r for r in results if r.get("category") == category_filter]

        sections = []
        act_ids_seen = set()
        for r in results:
            act_ids_seen.add(r["act_id"])
            section = {
                "act": r.get("full_title", ""),
                "act_id": r["act_id"],
                "section": r["section_number"],
                "section_title": r["section_title"],
                "text": r["text"],
                "relevance_score": round(float(r.get("rank", 0)), 2),
                "is_active": True,
            }
            if mapper and include_old_new_mapping:
                old_act_key = ACT_TO_OLD_ACT.get(r["act_id"])
                if old_act_key:
                    rev = mapper.get_mapping_details(
                        r["act_id"], r["section_number"], direction="reverse"
                    )
                    if rev:
                        section["old_law_mapping"] = {
                            "old_act": rev[0]["old_act"],
                            "old_section": rev[0]["old_section"],
                            "new_act": r["act_id"],
                            "new_section": r["section_number"],
                            "mapping_type": rev[0]["mapping_type"],
                            "change_description": mapper.format_reverse_change(
                                r["act_id"], r["section_number"]
                            ),
                        }
            sections.append(section)

        freshness = {"statute_index_built": "unknown", "act_last_verified": "unknown"}
        for aid in act_ids_seen:
            meta = index.get_act_meta(aid)
            if meta:
                freshness = format_data_freshness(
                    statute_index_built=meta.get("last_verified", ""),
                    act_last_verified=meta.get("last_verified", ""),
                )
                break

        confidence_score = 0.95 if sections else 0.0
        confidence = format_confidence(confidence_score)
        if sections:
            confidence["factors"] = [f"Found {len(sections)} matching sections"]
        else:
            confidence["factors"] = ["No sections matched the query"]

        return {
            "status": "success",
            "query": query,
            "total_results": len(sections),
            "sections": sections,
            "confidence": confidence,
            "data_freshness": freshness,
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query,
        }
