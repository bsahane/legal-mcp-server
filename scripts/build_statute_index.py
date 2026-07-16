#!/usr/bin/env python3
"""Build statute index from JSON files into SQLite FTS5."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from indian_legal_mcp_server.services.statute_index import build_index_from_json


def main():
    json_dir = "indian_legal_mcp_server/data/statutes"
    db_path = "indian_legal_mcp_server/data/statute_index.db"

    if not os.path.exists(json_dir):
        print(f"Error: JSON directory not found: {json_dir}")
        sys.exit(1)

    print(f"Building index from {json_dir} → {db_path}")
    build_index_from_json(json_dir, db_path)
    print("Index built successfully!")


if __name__ == "__main__":
    main()
