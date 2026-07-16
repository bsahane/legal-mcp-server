import re

CITATION_PATTERN = re.compile(r"\[([a-z_0-9]+)\.s\.([0-9A-Za-z()]+)\]")


def validate_citations(generated_text: str, indexed_sections: set) -> dict:
    found = CITATION_PATTERN.findall(generated_text)
    valid = []
    hallucinated = []

    for act_id, section in found:
        key = f"{act_id}.s.{section}"
        if key in indexed_sections:
            valid.append(key)
        else:
            hallucinated.append(key)

    cleaned_text = generated_text
    for h in hallucinated:
        cleaned_text = cleaned_text.replace(
            f"[{h}]", "[citation removed — not verified]"
        )

    return {
        "cleaned_text": cleaned_text,
        "valid_citations": valid,
        "hallucinated_citations": hallucinated,
        "warning": "Some citations were removed as they could not be verified."
        if hallucinated
        else None,
    }


def expand_citations(text: str) -> str:
    ACT_NAMES = {
        "bns_2023": "BNS",
        "bnss_2023": "BNSS",
        "bnsa_2023": "BNSA",
        "ipc_1860": "IPC",
        "crpc_1973": "CrPC",
        "hma_1955": "HMA",
        "dv_act_2005": "DV Act",
        "ni_1881": "NI Act",
        "limitation_act_1963": "Limitation Act",
        "cpc_1908": "CPC",
        "constitution": "Constitution",
        "contract_act_1872": "Contract Act",
        "consumer_protection_2019": "Consumer Protection Act",
        "hindu_succession_1956": "Hindu Succession Act",
        "special_marriage_1954": "Special Marriage Act",
        "rera_2016": "RERA",
        "it_act_2000": "IT Act",
    }

    def _replace(m: re.Match) -> str:
        act_id = m.group(1)
        section = m.group(2)
        short = ACT_NAMES.get(act_id, act_id)
        return f"Section {section} of the {short}"

    return CITATION_PATTERN.sub(_replace, text)
