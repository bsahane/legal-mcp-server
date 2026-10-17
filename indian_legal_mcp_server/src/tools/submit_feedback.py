"""
Error reporting tool — privacy-safe feedback submission.

Users report wrong tool outputs without sharing scenario text.
Zero-tolerance tool errors (limitation_calculator, bail_assessment)
trigger priority alerts.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

FEEDBACK_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "feedback.db"
)


def _get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(FEEDBACK_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(FEEDBACK_DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id TEXT PRIMARY KEY,
            tool_name TEXT,
            issue_type TEXT,
            description TEXT,
            expected_result TEXT,
            created_at TEXT
        )
    """)
    return conn


async def submit_feedback(
    tool_name: str,
    issue_type: str,
    description: str,
    expected_result: Optional[str] = None,
) -> dict:
    try:
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn = _get_conn()
        conn.execute(
            """INSERT INTO feedback (feedback_id, tool_name, issue_type, description, expected_result, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                feedback_id,
                tool_name,
                issue_type,
                description,
                expected_result,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        priority = ""
        if issue_type in ("wrong_limitation", "wrong_bail_classification"):
            priority = " This will be prioritized for immediate review."

        return {
            "status": "received",
            "feedback_id": feedback_id,
            "message": f"Thank you. Feedback logged for review.{priority}",
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
