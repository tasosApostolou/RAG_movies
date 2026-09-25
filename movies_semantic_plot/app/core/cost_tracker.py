from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Any, Dict, List


@dataclass
class RequestRecord:
    timestamp: datetime
    endpoint: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float


class CostTracker:
    def __init__(self):
        self._lock = Lock()
        self._total_requests = 0
        self._total_input_tokens = 0
        self._total_output_tokens = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        self._endpoint_stats: Dict[str, Dict] = {}
        self._recent_requests: List[RequestRecord] = []
        self._max_history = 100

    def add_request(
        self,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
    ) -> None:
        total_tokens = input_tokens + output_tokens

        with self._lock:
            self._total_requests += 1
            self._total_input_tokens += input_tokens
            self._total_output_tokens += output_tokens
            self._total_tokens += total_tokens
            self._total_cost += cost

            if endpoint not in self._endpoint_stats:
                self._endpoint_stats[endpoint] = {
                    "requests": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost": 0.0,
                }

            stats = self._endpoint_stats[endpoint]
            stats["requests"] += 1
            stats["input_tokens"] += input_tokens
            stats["output_tokens"] += output_tokens
            stats["total_tokens"] += total_tokens
            stats["cost"] += cost

            self._recent_requests.append(
                RequestRecord(
                    timestamp=datetime.now(),
                    endpoint=endpoint,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    cost=cost,
                )
            )

            self._recent_requests = self._recent_requests[-self._max_history:]

    def get_summary(self) -> dict:
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "total_input_tokens": self._total_input_tokens,
                "total_output_tokens": self._total_output_tokens,
                "total_tokens": self._total_tokens,
                "total_cost": round(self._total_cost, 6),
                "endpoints": self._endpoint_stats,
            }

    def get_recent_requests(self, n: int = 10) -> list[dict]:
        with self._lock:
            return [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "endpoint": r.endpoint,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "total_tokens": r.total_tokens,
                    "cost": round(r.cost, 6),
                }
                for r in self._recent_requests[-n:]
            ]



MODEL_PRICING = {
    "gpt-4.1-mini": {
        "input_per_1m": 0.40,
        "output_per_1m": 1.60,
    }
}

def _empty_usage() -> dict[str, int]:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }


def _get_usage_from_response(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage_metadata", None) or {}

    input_tokens = int(usage.get("input_tokens", 0) or 0)
    output_tokens = int(usage.get("output_tokens", 0) or 0)
    total_tokens = int(
        usage.get("total_tokens", input_tokens + output_tokens) or 0
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def _calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> float:
    pricing = MODEL_PRICING[model]

    input_cost = input_tokens / 1_000_000 * pricing["input_per_1m"]
    output_cost = output_tokens / 1_000_000 * pricing["output_per_1m"]

    return input_cost + output_cost

        