"""
3.48 Caching, Logging & Usage Monitoring Test
"""

from __future__ import annotations

import json

from rag_cache import (
    cache_stats,
    clear_cache,
    get_cached_answer,
    save_cached_answer,
)

from rag_logging import (
    log_rag_request,
    read_log_records,
)

from usage_monitoring import (
    calculate_usage,
    summarize_usage,
)


def main() -> None:

    print("=" * 60)
    print(
        "3.48 OBSERVABILITY TEST"
    )
    print("=" * 60)

    # ========================================================
    # CACHE
    # ========================================================

    print("\n1. CACHE TEST")

    clear_cache()

    question = (
        "When does an exporter "
        "need an export license?"
    )

    settings = {
        "top_k": 5,
        "model": "gemini-2.5-flash",
    }

    response = {
        "answer": (
            "An exporter may require "
            "an export license."
        ),
        "sources": [
            {
                "citation": "[1]",
                "source": (
                    "license_rules.txt"
                ),
                "chunk_id": (
                    "license-0"
                ),
                "chunk_index": 0,
            }
        ],
        "retrieval_count": 5,
        "top_score": 0.795,
        "supporting_chunks": 2,
        "threshold": 0.72,
    }

    before = get_cached_answer(
        question,
        settings,
    )

    print(
        "Cache before save:",
        before,
    )

    save_cached_answer(
        question,
        response,
        settings,
    )

    after = get_cached_answer(
        question,
        settings,
    )

    print(
        "Cache after save:",
        after is not None,
    )

    print(
        "Cache statistics:"
    )

    print(
        json.dumps(
            cache_stats(),
            indent=2,
        )
    )

    # ========================================================
    # USAGE
    # ========================================================

    print("\n2. USAGE TEST")

    usage = calculate_usage(
        question=question,
        prompt=(
            "Grounded RAG compliance "
            "prompt with retrieved "
            "context."
        ),
        answer=response["answer"],
        cache_hit=False,
    )

    print(
        json.dumps(
            usage,
            indent=2,
        )
    )

    # ========================================================
    # LOGGING
    # ========================================================

    print("\n3. LOGGING TEST")

    log_rag_request(
        request_id=(
            "sample-request-001"
        ),
        question=question,
        answer=response["answer"],
        sources=response["sources"],
        cache_hit=False,
        input_tokens=120,
        output_tokens=25,
        estimated_cost=0.000033,
        latency_ms=820.5,
        status="answered",
    )

    log_rag_request(
        request_id=(
            "sample-request-002"
        ),
        question=question,
        answer=response["answer"],
        sources=response["sources"],
        cache_hit=True,
        input_tokens=0,
        output_tokens=0,
        estimated_cost=0.0,
        latency_ms=3.4,
        status="cache_hit",
    )

    records = read_log_records()

    print(
        "Total log records:",
        len(records),
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n4. USAGE SUMMARY")

    summary = summarize_usage(
        records
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    cache_passed = (
        before is None
        and after is not None
    )

    summary_passed = (
        summary[
            "total_requests"
        ]
        >= 2
        and summary[
            "cache_hits"
        ]
        >= 1
    )

    print("\n5. VALIDATION")

    print(
        "Cache test:",
        "PASS"
        if cache_passed
        else "FAIL",
    )

    print(
        "Logging test:",
        "PASS"
        if len(records) >= 2
        else "FAIL",
    )

    print(
        "Usage summary test:",
        "PASS"
        if summary_passed
        else "FAIL",
    )

    print(
        "\nALL 3.48 TESTS COMPLETED"
    )


if __name__ == "__main__":
    main()