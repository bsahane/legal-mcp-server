import json
from pathlib import Path
from typing import Optional

MAPPING_TYPES = {"direct", "modified", "split", "merged", "new", "repealed"}


class SectionMapper:
    def __init__(self, mapping_path: Optional[str] = None):
        self._forward: dict[str, list[dict]] = {}
        self._reverse: dict[str, list[dict]] = {}
        if mapping_path and Path(mapping_path).exists():
            with open(mapping_path) as f:
                data = json.load(f)
                for item in data:
                    fwd_key = f"{item['old_act']}.s.{item['old_section']}"
                    rev_key = f"{item['new_act']}.s.{item['new_section']}"
                    if fwd_key not in self._forward:
                        self._forward[fwd_key] = []
                    self._forward[fwd_key].append(item)
                    if rev_key not in self._reverse:
                        self._reverse[rev_key] = []
                    self._reverse[rev_key].append(item)

    def lookup_old(self, old_act: str, old_section: str) -> Optional[list[dict]]:
        key = f"{old_act}.s.{old_section}"
        return self._forward.get(key)

    def lookup_new(self, new_act: str, new_section: str) -> Optional[list[dict]]:
        key = f"{new_act}.s.{new_section}"
        return self._reverse.get(key)

    def get_new_section(self, old_act: str, old_section: str) -> Optional[list[str]]:
        items = self.lookup_old(old_act, old_section)
        if items:
            return [item["new_section"] for item in items]
        return None

    def get_old_section(self, new_act: str, new_section: str) -> Optional[list[str]]:
        items = self.lookup_new(new_act, new_section)
        if items:
            return [item["old_section"] for item in items]
        return None

    def format_change(self, old_act: str, old_section: str) -> Optional[str]:
        items = self.lookup_old(old_act, old_section)
        if not items:
            return None
        item = items[0]
        new = item["new_section"]
        mtype = item["mapping_type"]
        changes = item.get("changes", "")
        if mtype == "direct":
            return f"now Section {new}"
        elif mtype == "split":
            return f"now Sections {new} - {changes}"
        elif mtype == "merged":
            return f"now Section {new} (merged - {changes})"
        elif mtype == "modified":
            return f"now Section {new} (modified - {changes})"
        elif mtype == "repealed":
            return "repealed — no equivalent in new law"
        elif mtype == "new":
            return "new provision — no equivalent in old law"
        return f"\u2192 Section {new}"

    def format_reverse_change(self, new_act: str, new_section: str) -> Optional[str]:
        items = self.lookup_new(new_act, new_section)
        if not items:
            return None
        item = items[0]
        old = item["old_section"]
        return f"formerly Section {old} under {item['old_act']}"

    def get_mapping_details(
        self, act: str, section: str, direction: str = "forward"
    ) -> Optional[list[dict]]:
        if direction == "reverse":
            return self.lookup_new(act, section)
        return self.lookup_old(act, section)


def build_mapping_from_json(json_path: str) -> dict:
    with open(json_path) as f:
        return json.load(f)
