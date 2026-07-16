import json
import os
from typing import Optional
from indian_legal_mcp_server.services.search_engine import StatuteSearchEngine
from indian_legal_mcp_server.config import settings


class StatuteIndex:
    def __init__(self, search_engine: StatuteSearchEngine):
        self.engine = search_engine

    @classmethod
    def from_default_path(cls) -> "StatuteIndex":
        engine = StatuteSearchEngine(settings.STATUTE_INDEX_PATH)
        return cls(engine)

    def search(
        self, query: str, act_filter: Optional[str] = None, max_results: int = 10
    ) -> list[dict]:
        return self.engine.search(query, act_filter, max_results)

    def get_section(self, act_id: str, section_number: str) -> Optional[dict]:
        return self.engine.get_section(act_id, section_number)

    def get_act_meta(self, act_id: str) -> Optional[dict]:
        return self.engine.get_act_meta(act_id)

    def get_indexed_sections(self) -> set:
        rows = self.engine.conn.execute(
            "SELECT act_id || '.s.' || section_number FROM statute_fts"
        ).fetchall()
        return {r[0] for r in rows}

    def get_indexed_acts(self) -> list[str]:
        rows = self.engine.conn.execute(
            "SELECT DISTINCT act_id FROM statute_fts"
        ).fetchall()
        return [r[0] for r in rows]

    def close(self):
        self.engine.close()


def build_index_from_json(json_dir: str, db_path: str):
    import sqlite3

    conn = sqlite3.connect(db_path)
    conn.execute("""
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
    conn.execute("""
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

    for filename in os.listdir(json_dir):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(json_dir, filename)
        with open(filepath) as f:
            act = json.load(f)

        conn.execute(
            """INSERT OR REPLACE INTO statute_meta
               (act_id, full_title, short_title, year, category, enforcement_date, is_active, source_url, last_verified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                act["act_id"],
                act.get("full_title", ""),
                act.get("short_title", ""),
                act.get("year", 0),
                act.get("category", ""),
                act.get("enforcement_date", ""),
                1 if act.get("is_active", True) else 0,
                act.get("source_url", ""),
                act.get("last_verified", ""),
            ),
        )

        for section in act.get("sections", []):
            conn.execute(
                """INSERT INTO statute_fts (act_id, section_number, section_title, text, keywords, chapter)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    act["act_id"],
                    section["section_number"],
                    section.get("section_title", ""),
                    section.get("text", ""),
                    " ".join(section.get("keywords", [])),
                    section.get("chapter", ""),
                ),
            )

    conn.commit()
    conn.close()
