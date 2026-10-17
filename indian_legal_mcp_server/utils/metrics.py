import time
from collections import defaultdict
from typing import Optional


class ToolMetrics:
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self._local: list[dict] = []

    def record_call(
        self,
        tool_name: str,
        status: str,
        duration_ms: int,
        confidence_score: float,
        classification: str = None,
    ):
        self._local.append(
            {
                "tool_name": tool_name,
                "status": status,
                "duration_ms": duration_ms,
                "confidence_score": confidence_score,
                "classification": classification,
                "timestamp": time.time(),
            }
        )

    def get_daily_summary(self) -> dict:
        today = time.time() - 86400
        recent = [c for c in self._local if c["timestamp"] > today]
        calls_per_tool = defaultdict(int)
        status_counts = defaultdict(int)
        total_duration = 0
        confidences = []

        for call in recent:
            calls_per_tool[call["tool_name"]] += 1
            status_counts[call["status"]] += 1
            total_duration += call["duration_ms"]
            if call["confidence_score"]:
                confidences.append(call["confidence_score"])

        return {
            "total_calls": len(recent),
            "calls_per_tool": dict(calls_per_tool),
            "status_breakdown": dict(status_counts),
            "avg_response_time_ms": total_duration / len(recent) if recent else 0,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
        }


_metrics: Optional[ToolMetrics] = None


def get_metrics() -> ToolMetrics:
    global _metrics
    if _metrics is None:
        _metrics = ToolMetrics()
    return _metrics
