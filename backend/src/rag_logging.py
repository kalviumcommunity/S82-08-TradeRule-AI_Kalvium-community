"""
3.48 Structured RAG Logging

Stores one JSON object per request in a JSONL file.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ============================================================
# LOG CONFIGURATION
# ============================================================

LOG_DIR = Path(
    os.getenv(
        "RAG_LOG_DIR",
        "logs",
    )
)

LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

LOG_FILE = (
    LOG_DIR
    / "rag_requests.jsonl"
)


# ============================================================
# LOGGER
# ============================================================

logger = logging.getLogger(
    "traderule_rag"
)

logger.setLevel(
    logging.INFO
)

logger.propagate = False


if not logger.handlers:

    file_handler = (
        logging.FileHandler(
            LOG_FILE,
            encoding="utf-8",
        )
    )

    file_handler.setFormatter(
        logging.Formatter(
            "%(message)s"
        )
    )

    logger.addHandler(
        file_handler
    )


# ============================================================
# LOG REQUEST
# ============================================================

def log_rag_request(
    *,
    request_id: str,
    question: str,
    answer: str = "",
    sources: list[dict[str, Any]]
    | None = None,
    cache_hit: bool = False,
    input_tokens: int = 0,
    output_tokens: int = 0,
    estimated_cost: float = 0.0,
    latency_ms: float = 0.0,
    status: str = "unknown",
    error: str | None = None,
) -> dict[str, Any]:
    """
    Write one structured request record.
    """

    record = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),

        "request_id": request_id,

        "question": question,

        "answer_preview": (
            answer[:180]
            if answer
            else ""
        ),

        "sources": sources or [],

        "cache_hit": cache_hit,

        "input_tokens": int(
            input_tokens
        ),

        "output_tokens": int(
            output_tokens
        ),

        "estimated_cost": round(
            float(
                estimated_cost
            ),
            6,
        ),

        "latency_ms": round(
            float(latency_ms),
            2,
        ),

        "status": status,

        "error": error,
    }

    logger.info(
        json.dumps(
            record,
            ensure_ascii=False,
        )
    )

    return record


# ============================================================
# READ LOGS
# ============================================================

def read_log_records() -> list[
    dict[str, Any]
]:
    """
    Read valid JSON records from the log file.
    """

    if not LOG_FILE.exists():
        return []

    records: list[
        dict[str, Any]
    ] = []

    with LOG_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line = line.strip()

            if not line:
                continue

            try:

                record = json.loads(
                    line
                )

                if isinstance(
                    record,
                    dict,
                ):
                    records.append(
                        record
                    )

            except json.JSONDecodeError:
                continue

    return records