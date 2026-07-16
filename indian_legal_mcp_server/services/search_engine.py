import sqlite3
import re
from typing import Optional

ABBREVIATION_MAP = {
    "IPC": "Indian Penal Code 1860",
    "BNS": "Bharatiya Nyaya Sanhita 2023",
    "CrPC": "Code of Criminal Procedure 1973",
    "BNSS": "Bharatiya Nagarik Suraksha Sanhita 2023",
    "IEA": "Indian Evidence Act 1872",
    "BNSA": "Bharatiya Sakshya Adhiniyam 2023",
    "HMA": "Hindu Marriage Act 1955",
    "DV Act": "Protection of Women from Domestic Violence Act 2005",
    "NI Act": "Negotiable Instruments Act 1881",
    "CPC": "Code of Civil Procedure 1908",
    "TPA": "Transfer of Property Act 1882",
    "CPA": "Consumer Protection Act 2019",
    "RERA": "Real Estate Regulation and Development Act 2016",
    "POSH": "Prevention of Sexual Harassment Act 2013",
    "NDPS": "Narcotic Drugs and Psychotropic Substances Act 1985",
    "POCSO": "Protection of Children from Sexual Offences Act 2012",
    "IT Act": "Information Technology Act 2000",
    "DPDP": "Digital Personal Data Protection Act 2023",
    "IBC": "Insolvency and Bankruptcy Code 2016",
    "RTI": "Right to Information Act 2005",
    "SMA": "Special Marriage Act 1954",
    "Limitation Act": "Limitation Act 1963",
    "Special Marriage Act": "Special Marriage Act 1954",
    "s.": "section ",
    "u/s": "under section",
    "r/w": "read with",
    "Sec.": "Section",
}


def expand_abbreviations(query: str) -> str:
    expanded = query
    for abbrev, full in sorted(ABBREVIATION_MAP.items(), key=lambda x: -len(x[0])):
        expanded = re.sub(
            rf"\b{re.escape(abbrev)}\b", full, expanded, flags=re.IGNORECASE
        )
    return expanded


class StatuteSearchEngine:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._ensure_fts_table()

    def _ensure_fts_table(self):
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

    def search(
        self, query: str, act_filter: Optional[str] = None, max_results: int = 10
    ) -> list[dict]:
        exact_match = self._try_exact_section_lookup(query)
        if exact_match:
            return exact_match
        query = expand_abbreviations(query)

        sql = """
            SELECT *, rank FROM statute_fts
            WHERE statute_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        params = [query, max_results]

        if act_filter:
            sql = """
                SELECT *, rank FROM statute_fts
                WHERE statute_fts MATCH ? AND act_id = ?
                ORDER BY rank
                LIMIT ?
            """
            params = [query, act_filter, max_results]

        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def _try_exact_section_lookup(self, query: str) -> Optional[list[dict]]:
        patterns = [
            r"(?:section|sec|s|s\.)\s*(\d+[A-Za-z]*)",
            r"(?:BNS|BNSS|IPC|CrPC|HMA|DV Act|NI Act|Limitation Act|SMA|Special Marriage Act)\s*(\d+[A-Za-z]*)",
            r"(?:DV Act)\s*(\d+[A-Za-z]*)",
        ]
        for pattern in patterns:
            m = re.search(pattern, query, re.IGNORECASE)
            if m:
                section_num = m.group(1)
                rows = self.conn.execute(
                    "SELECT * FROM statute_fts WHERE section_number = ? ORDER BY rank LIMIT 5",
                    [section_num],
                ).fetchall()
                if rows:
                    return [dict(r) for r in rows]
        return None

    def get_act_meta(self, act_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM statute_meta WHERE act_id = ?", [act_id]
        ).fetchone()
        return dict(row) if row else None

    def get_section(self, act_id: str, section_number: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM statute_fts WHERE act_id = ? AND section_number = ?",
            [act_id, section_number],
        ).fetchone()
        return dict(row) if row else None

    def close(self):
        self.conn.close()
