"""
Consolidated legal search tool.

Routes to internal implementations based on search type.
v0.1: type="statute" only (FTS5 section-level search)
v0.5: + "concept"
v1.0: + "topic", "precedent"
"""

from typing import Optional

from indian_legal_mcp_server.src.tools._impl.statute_search import (
    statute_search as _statute_search,
)
from indian_legal_mcp_server.src.tools.legal_concepts import legal_concepts


async def legal_search(
    query: str,
    type: str = "statute",
    act_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    include_old_new_mapping: bool = True,
    max_results: int = 10,
    include_case_law: bool = True,
) -> dict:
    if type == "statute":
        return await _statute_search(
            query=query,
            act_filter=act_filter,
            category_filter=category_filter,
            include_old_new_mapping=include_old_new_mapping,
            max_results=max_results,
        )
    elif type == "concept":
        return await legal_concepts(
            concept=query,
            include_case_law=include_case_law,
            max_related_sections=max_results,
        )

    return {
        "status": "error",
        "error": f"Search type '{type}' not available. Supported types: statute, concept",
        "query": query,
    }
