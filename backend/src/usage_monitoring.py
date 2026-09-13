"""
3.48 Usage Monitoring

Tracks approximate token usage and model cost.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


# ============================================================
# APPROXIMATE MODEL COST
# ============================================================

MODEL_INPUT_COST_PER_1K = 0.00015

MODEL_OUTPUT_COST_PER_1K = 0.00060


# ============================================================
# TOKEN ESTIMATION
# ============================================================

def estimate_tokens(
    text: str,
) -> int:
    """
    Rough token estimate.

    Approximation:
        1 token ~= 4 characters
    """

    if not text:
        return 0

    return max(
        1,
        (len(text) + 3) // 4,
    )


# ============================================================
# COST
# ============================================================

def estimate_cost(
    input_tokens: int,
    output_tokens: int,
) -> float:
    """
    Estimate model cost from token counts.
    """

    input_cost = (
        input_tokens
        / 1000
        * MODEL_INPUT_COST_PER_1K
    )

    output_cost = (
        output_tokens
        / 1000
        * MODEL_OUTPUT_COST_PER_1K
    )

    return round(
        input_cost + output_cost,
        6,
    )


# ============================================================
# REQUEST USAGE
# ============================================================

def calculate_usage(
    *,
    question: str,
    prompt: str = "",
    answer: str = "",
    cache_hit: bool = False,
) -> dict[str, Any]:
    """
    Calculate approximate usage for one request.

    Cached requests consume no new model tokens,
    so their estimated model cost is zero.
    """

    if cache_hit:

        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost": 0.0,
            "cache_hit": True,
        }

    input_text = (
        prompt
        if prompt
        else question
    )

    input_tokens = (
        estimate_tokens(
            input_text
        )
    )

    output_tokens = (
        estimate_tokens(
            answer
        )
    )

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost": estimate_cost(
            input_tokens,
            output_tokens,
        ),
        "cache_hit": False,
    }


# ============================================================
# SUMMARY
# ============================================================

def summarize_usage(
    log_records: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    """
    Produce an aggregate usage report.
    """

    total_requests = len(
        log_records
    )

    cache_hits = sum(
        1
        for record in log_records
        if record.get(
            "cache_hit",
            False,
        )
    )

    cache_misses = (
        total_requests
        - cache_hits
    )

    total_input_tokens = sum(
        int(
            record.get(
                "input_tokens",
                0,
            )
        )
        for record in log_records
    )

    total_output_tokens = sum(
        int(
            record.get(
                "output_tokens",
                0,
            )
        )
        for record in log_records
    )

    total_cost = sum(
        float(
            record.get(
                "estimated_cost",
                0,
            )
        )
        for record in log_records
    )

    total_latency = sum(
        float(
            record.get(
                "latency_ms",
                0,
            )
        )
        for record in log_records
    )

    average_latency = (
        total_latency
        / max(
            total_requests,
            1,
        )
    )

    return {
        "total_requests": (
            total_requests
        ),

        "cache_hits": (
            cache_hits
        ),

        "cache_misses": (
            cache_misses
        ),

        "cache_hit_rate": round(
            cache_hits
            / max(
                total_requests,
                1,
            ),
            2,
        ),

        "total_input_tokens": (
            total_input_tokens
        ),

        "total_output_tokens": (
            total_output_tokens
        ),

        "total_estimated_cost": round(
            total_cost,
            6,
        ),

        "average_latency_ms": round(
            average_latency,
            2,
        ),
    }


# ============================================================
# SAVE SUMMARY
# ============================================================

def save_usage_summary(
    summary: dict[str, Any],
    output_path: str = (
        "logs/usage_summary.json"
    ),
) -> None:
    """
    Save the usage report to JSON.
    """

    path = Path(
        output_path
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            indent=2,
        )