#!/usr/bin/env python3
"""Validate all statute JSON files for correctness.

Checks:
1. Every JSON file is valid JSON
2. Every act has: act_id, full_title, year, category, sections[], versions[]
3. Every section has: section_number, section_title, text (non-empty)
4. No duplicate section numbers within an act
5. All act_ids are unique across the corpus
6. All dates are valid ISO format
7. versions field is present (empty array in v0.1, architecture-ready)
"""

import json
import os
import sys
from datetime import datetime


def validate():
    data_dir = "indian_legal_mcp_server/data/statutes"
    errors = []

    if not os.path.exists(data_dir):
        print(f"Error: Directory not found: {data_dir}")
        sys.exit(1)

    act_ids = set()
    total_sections = 0

    for filename in sorted(os.listdir(data_dir)):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(data_dir, filename)
        try:
            with open(filepath) as f:
                act = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{filename}: Invalid JSON — {e}")
            continue

        for field in [
            "act_id",
            "full_title",
            "year",
            "category",
            "sections",
            "versions",
        ]:
            if field not in act:
                errors.append(f"{filename}: Missing required field '{field}'")

        if act.get("versions") is not None and not isinstance(act["versions"], list):
            errors.append(f"{filename}: 'versions' must be an array")

        if act.get("act_id") in act_ids:
            errors.append(f"{filename}: Duplicate act_id '{act['act_id']}'")
        act_ids.add(act.get("act_id"))

        for date_field in ["enforcement_date", "last_verified"]:
            val = act.get(date_field)
            if val:
                try:
                    datetime.fromisoformat(val)
                except ValueError:
                    errors.append(
                        f"{filename}: Invalid ISO date in '{date_field}': {val}"
                    )

        seen_sections = set()
        for i, section in enumerate(act.get("sections", [])):
            for field in ["section_number", "section_title", "text"]:
                if field not in section:
                    errors.append(f"{filename} section {i}: Missing field '{field}'")

            sn = section.get("section_number")
            if sn:
                if sn in seen_sections:
                    errors.append(f"{filename}: Duplicate section '{sn}'")
                seen_sections.add(sn)

            if not section.get("text", "").strip():
                errors.append(f"{filename} s.{sn}: Empty text field")

        total_sections += len(act.get("sections", []))

    if errors:
        print(f"VALIDATION FAILED: {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"All {len(act_ids)} acts validated successfully!")
    print(f"Total sections indexed: {total_sections}")


if __name__ == "__main__":
    validate()
