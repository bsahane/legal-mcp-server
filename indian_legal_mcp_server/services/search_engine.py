import re
import sqlite3
from typing import Optional

ACT_ABBREVS = {
    "BNS": "bns_2023",
    "BNSS": "bnss_2023",
    "BNSA": "bsa_2023",
    "BSA": "bsa_2023",
    "IPC": "bns_2023",
    "IPC 1860": "bns_2023",
    "BNSS 2023": "bnss_2023",
    "BNS 2023": "bns_2023",
    "BNSSA": "bsa_2023",
}

ACT_ABBREVS_TO_ACT_ID = {
    "IPC": "bns_2023",
    "CRPC": "bnss_2023",
    "BNS": "bns_2023",
    "BNSS": "bnss_2023",
    "BSA": "bsa_2023",
    "EVIDENCE": "bsa_2023",
    "NI": "ni_act_1881",
    "CPC": "cpc_1908",
    "CONSUMER": "cpc_1908",
    "CPA": "cpa_2019",
    "LIMITATION": "limitation_act_1963",
    "LIMITATION ACT": "limitation_act_1963",
    "DV": "dv_act_2005",
    "SMA": "special_marriage_act_1954",
    "HMA": "hmm_1955",
}


def expand_abbreviations(query: str) -> str:
    expanded = query
    for old, new in ACT_ABBREVS.items():
        expanded = re.sub(
            r"\b" + re.escape(old) + r"\b", new, expanded, flags=re.IGNORECASE
        )
    expanded = re.sub(r"\s*Section\s+", " ", expanded, flags=re.IGNORECASE)
    expanded = re.sub(r"\s+act\b", " ", expanded, flags=re.IGNORECASE)
    return expanded.strip()


class StatuteSearchEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_fts_table()

    def _ensure_fts_table(self):
        """Create the FTS table and metadata table if they do not exist.

        Run in __init__ so a fresh or accidentally-empty index is usable
        rather than raising OperationalError on the first query.
        """
        self.conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS statute_fts USING fts5(
                act_id,
                section_number,
                section_title,
                text,
                keywords,
                chapter,
                tokenize='porter unicode61'
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS statute_meta (
                act_id TEXT PRIMARY KEY,
                full_title TEXT,
                short_title TEXT,
                year INTEGER,
                category TEXT,
                enforcement_date TEXT,
                is_active INTEGER,
                source_url TEXT,
                last_verified TEXT
            )
        """)

    def _build_query(
        self, match_term: str, where: str, params: list
    ) -> tuple[str, list]:
        """Shared SELECT for both search paths.

        GROUP BY deduplicates the index, which stores one identical row per
        section per enrichment pass. Without it, LIMIT truncates a run of
        duplicates and the caller never sees a second distinct section.
        MIN(rank) aliases the score into the table's `rank` column so callers
        read it uniformly; a bare `rank` outside MATCH returns NULL.
        """
        sql = f"""
            SELECT *, MIN(rank) AS rank
            FROM statute_fts
            WHERE statute_fts MATCH ? AND {where}
            GROUP BY act_id, section_number
            ORDER BY MIN(rank) ASC
            LIMIT ?
        """  # nosec B608 -- {where} is a caller-supplied whitelist fragment
        return sql, [match_term, *params]

    def search(
        self, query: str, act_filter: Optional[str] = None, max_results: int = 10
    ) -> list[dict]:
        exact_match = self._try_exact_section_lookup(query, act_filter)
        if exact_match is not None:
            return exact_match

        where = "1=1"
        params: list = []
        if act_filter:
            where = "act_id = ?"
            params.append(act_filter)
        sql, full_params = self._build_query(expand_abbreviations(query), where, params)
        full_params.append(max_results)
        rows = self.conn.execute(sql, full_params).fetchall()
        return [dict(r) for r in rows]

    def _try_exact_section_lookup(
        self, query: str, act_filter: str = None
    ) -> Optional[list[dict]]:
        match = re.match(
            r"(?:BNS|BNSS|IPC|CRPC|CONSUMER)\s*(?:1860|1973)?\s*section\s+(\d+)",
            query,
            re.IGNORECASE,
        )
        if match:
            section_num = match.group(1)
            act_id = act_filter or self._resolve_act_filter(query)
            return self.search_by_section(section_num, act_id)

        match = re.match(
            r"(?:BNS|BNSS|IPC|CRPC|CONSUMER)\s*(?:1860|1973)?\s+(\d+)",
            query,
            re.IGNORECASE,
        )
        if match:
            section_num = match.group(1)
            act_id = act_filter or self._resolve_act_filter(query)
            return self.search_by_section(section_num, act_id)

        match = re.match(r"section\s+(\d+)", query, re.IGNORECASE)
        if match:
            section_num = match.group(1)
            return self.search_by_section(section_num)

        return None

    def _resolve_act_filter(self, query: str) -> Optional[str]:
        q_upper = query.upper()
        if "BNS" in q_upper or "IPC" in q_upper:
            return "bns_2023"
        if "BNSS" in q_upper or "CRPC" in q_upper:
            return "bnss_2023"
        if "CONSUMER" in q_upper:
            return "consumer_2019"
        return None

    def search_by_section(self, section_number: str, act_id: str = None) -> list[dict]:
        """Exact section-number lookup.

        Runs a real MATCH rather than `SELECT *, rank`: outside MATCH the
        rank column is NULL, which silently zeroes every relevance score.
        """
        where = "section_number = ?"
        params: list = [section_number]
        if act_id:
            where += " AND act_id = ?"
            params.append(act_id)
        sql, full_params = self._build_query(section_number, where, params)
        full_params.append(10)
        rows = self.conn.execute(sql, full_params).fetchall()
        return [dict(r) for r in rows]

    def get_act_meta(self, act_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM statute_meta WHERE act_id = ? LIMIT 1", (act_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_section(self, act_id: str, section_number: str) -> Optional[dict]:
        """One row by act + section.

        Uses _build_query so the score is a real MATCH rank: outside MATCH the
        FTS rank column is NULL, which would silently zero every relevance
        downstream. MIN(rank) aliases that value into the table's own
        `rank` column so callers read it uniformly.
        """
        match_term = f"{act_id} {section_number}"
        sql, full_params = self._build_query(
            match_term, "section_number = ? AND act_id = ?", [section_number, act_id]
        )
        full_params.append(1)
        rows = self.conn.execute(sql, full_params).fetchall()
        return dict(rows[0]) if rows else None

    def close(self):
        self.conn.close()
