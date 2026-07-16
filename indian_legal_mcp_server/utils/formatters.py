from datetime import date, datetime


def format_date(d: date) -> str:
    return d.isoformat()


def format_timestamp(dt: datetime) -> str:
    return dt.isoformat()


def format_section_ref(act_id: str, section: str) -> str:
    ACT_SHORT = {
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
    }
    short = ACT_SHORT.get(act_id, act_id)
    return f"{short} s.{section}"


def format_confidence(score: float) -> dict:
    if score > 0.9:
        level = "high"
    elif score > 0.7:
        level = "medium"
    else:
        level = "low"
    return {"score": round(score, 2), "level": level}


def format_data_freshness(
    statute_index_built: str = "", act_last_verified: str = ""
) -> dict:
    return {
        "statute_index_built": statute_index_built or "unknown",
        "act_last_verified": act_last_verified or "unknown",
    }
