"""
3.48 Usage Report Generator
"""

from __future__ import annotations

import json

from rag_logging import (
    read_log_records,
)

from usage_monitoring import (
    save_usage_summary,
    summarize_usage,
)


def main() -> None:

    records = read_log_records()

    summary = summarize_usage(
        records
    )

    save_usage_summary(
        summary
    )

    print(
        "=" * 60
    )

    print(
        "TradeRule AI Usage Report"
    )

    print(
        "=" * 60
    )

    print(
        json.dumps(
            summary,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()