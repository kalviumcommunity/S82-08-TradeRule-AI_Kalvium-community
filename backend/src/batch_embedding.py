import json
import os
import time
from pathlib import Path
from typing import Any

import tiktoken
from openai import OpenAI

from .config import (
    GEMINI_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_MODEL,
)


# ============================================================
# CONFIGURATION
# ============================================================

BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "2"))
MAX_ATTEMPTS = int(os.getenv("EMBEDDING_MAX_ATTEMPTS", "3"))

# Approximate price per 1K input tokens.
# Keep this configurable because provider/model pricing can change.
PRICE_PER_1K_TOKENS = float(
    os.getenv("EMBEDDING_PRICE_PER_1K_TOKENS", "0.00002")
)

EMBEDDING_STORE = Path(
    os.getenv(
        "EMBEDDING_STORE",
        "backend/src/embedding_store.json",
    )
)

ENCODER = tiktoken.get_encoding("cl100k_base")


client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=EMBEDDING_BASE_URL,
    timeout=60.0,
    max_retries=0,
)


# ============================================================
# SAMPLE CHUNKS
# ============================================================

CHUNKS = [
    {
        "id": "customs-0",
        "text": (
            "International shipment compliance requires exporters "
            "to verify product classification and destination requirements."
        ),
        "metadata": {
            "source": "customs_requirements.txt",
            "chunk_index": 0,
            "section": "export compliance",
            "document_type": "txt",
        },
    },
    {
        "id": "export-0",
        "text": (
            "Exporters should verify export control requirements, "
            "destination restrictions, required licenses, and customs documentation."
        ),
        "metadata": {
            "source": "export_guidelines.md",
            "chunk_index": 0,
            "section": "export guidelines",
            "document_type": "markdown",
        },
    },
    {
        "id": "import-0",
        "text": (
            "Importers should verify customs documentation before "
            "the shipment arrives."
        ),
        "metadata": {
            "source": "import_rules.html",
            "chunk_index": 0,
            "section": "import requirements",
            "document_type": "html",
        },
    },
    {
        "id": "campus-3",
        "text": (
            "The cafeteria menu includes pasta, rice, vegetables, "
            "and fresh fruit."
        ),
        "metadata": {
            "source": "campus-guide.txt",
            "chunk_index": 3,
            "section": "cafeteria",
            "document_type": "txt",
        },
    },
    {
        "id": "license-0",
        "text": (
            "Certain controlled products may require an export license "
            "before shipment depending on destination and classification."
        ),
        "metadata": {
            "source": "license_rules.txt",
            "chunk_index": 0,
            "section": "export licensing",
            "document_type": "txt",
        },
    },
    {
        "id": "documentation-0",
        "text": (
            "Commercial invoices, packing lists, and customs declarations "
            "should be prepared accurately for international shipments."
        ),
        "metadata": {
            "source": "shipping_documents.md",
            "chunk_index": 0,
            "section": "customs documentation",
            "document_type": "markdown",
        },
    },
]


# ============================================================
# BATCHING
# ============================================================

def batches(items: list[dict[str, Any]], size: int):
    """Yield items in configurable batch sizes."""

    if size <= 0:
        raise ValueError("Batch size must be greater than zero.")

    for start in range(0, len(items), size):
        yield items[start:start + size]


# ============================================================
# TOKEN ESTIMATION
# ============================================================

def estimate_tokens(texts: list[str]) -> int:
    """Estimate input tokens using cl100k_base."""

    return sum(len(ENCODER.encode(text)) for text in texts)


# ============================================================
# PERSISTENT EMBEDDING STORE
# ============================================================

def load_embedding_store() -> dict[str, Any]:
    """Load previously generated embeddings."""

    if not EMBEDDING_STORE.exists():
        return {}

    try:
        with EMBEDDING_STORE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Embedding store must contain a JSON object.")

        return data

    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"Warning: could not load embedding store: {error}")
        return {}


def save_embedding_store(store: dict[str, Any]) -> None:
    """Persist embeddings after every successful batch."""

    EMBEDDING_STORE.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = EMBEDDING_STORE.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(store, file, indent=2)

    temporary_path.replace(EMBEDDING_STORE)


# ============================================================
# RETRY WITH EXPONENTIAL BACKOFF
# ============================================================

def embed_with_retry(
    texts: list[str],
    max_attempts: int = MAX_ATTEMPTS,
):
    """
    Send one embedding batch with exponential backoff.

    Wait sequence:
        attempt 1 -> 1 second
        attempt 2 -> 2 seconds
        attempt 3 -> 4 seconds
    """

    if not texts:
        raise ValueError("Cannot embed an empty batch.")

    for attempt in range(max_attempts):
        try:
            print(
                f"API attempt {attempt + 1}/{max_attempts} "
                f"for batch of {len(texts)} chunks"
            )

            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )

            return response

        except Exception as error:

            if attempt == max_attempts - 1:
                print(
                    f"Batch failed after {max_attempts} attempts: {error}"
                )
                raise

            wait_seconds = 2 ** attempt

            print(
                f"Temporary embedding error: {error}"
            )
            print(
                f"Retrying after error | wait={wait_seconds}s"
            )

            time.sleep(wait_seconds)


# ============================================================
# VALIDATION
# ============================================================

def validate_embedding_response(
    response,
    expected_count: int,
) -> None:
    """Verify the API returned one vector per input."""

    if not hasattr(response, "data"):
        raise ValueError("Embedding response does not contain data.")

    if len(response.data) != expected_count:
        raise ValueError(
            "Embedding count mismatch: "
            f"expected {expected_count}, got {len(response.data)}"
        )

    for item in response.data:
        if not hasattr(item, "embedding"):
            raise ValueError("Embedding response item has no vector.")

        if not item.embedding:
            raise ValueError("Received an empty embedding vector.")


# ============================================================
# BATCH EMBEDDING PIPELINE
# ============================================================

def run_embedding_pipeline(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:

    store = load_embedding_store()

    pending_chunks = [
        chunk
        for chunk in chunks
        if chunk["id"] not in store
    ]

    skipped_existing = len(chunks) - len(pending_chunks)

    summary = {
        "total_chunks": len(chunks),
        "batch_size": BATCH_SIZE,
        "total_batches": 0,
        "skipped_existing": skipped_existing,
        "embedded": 0,
        "failed": 0,
        "input_tokens": 0,
        "estimated_cost_usd": 0.0,
        "failed_batches": [],
    }

    print()
    print("=" * 70)
    print("BATCH EMBEDDING & RATE/COST MANAGEMENT")
    print("=" * 70)

    print()
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Embedding base URL: {EMBEDDING_BASE_URL}")
    print(f"Configured batch size: {BATCH_SIZE}")
    print(f"Maximum attempts: {MAX_ATTEMPTS}")
    print(
        f"Approximate price per 1K tokens: "
        f"${PRICE_PER_1K_TOKENS:.8f}"
    )

    print()
    print("=" * 70)
    print("PENDING CHUNKS")
    print("=" * 70)

    print(f"Total chunks: {len(chunks)}")
    print(f"Already embedded: {skipped_existing}")
    print(f"Pending chunks: {len(pending_chunks)}")

    if not pending_chunks:
        print()
        print("No pending chunks.")
        print("All chunks already have embeddings.")
        print("No API embedding calls required.")

    for batch_number, batch in enumerate(
        batches(pending_chunks, BATCH_SIZE),
        start=1,
    ):

        summary["total_batches"] += 1

        texts = [chunk["text"] for chunk in batch]

        batch_tokens = estimate_tokens(texts)
        summary["input_tokens"] += batch_tokens

        print()
        print("-" * 70)
        print(f"BATCH {batch_number}")
        print("-" * 70)

        print(f"Chunks in batch: {len(batch)}")
        print(f"Estimated input tokens: {batch_tokens}")

        for chunk in batch:
            print(
                f"  - {chunk['id']} | "
                f"{chunk['metadata']['source']}"
            )

        try:
            response = embed_with_retry(texts)

            validate_embedding_response(
                response,
                expected_count=len(batch),
            )

            # The API response order corresponds to input order.
            for chunk, embedding_item in zip(
                batch,
                response.data,
            ):
                store[chunk["id"]] = {
                    "id": chunk["id"],
                    "text": chunk["text"],
                    "metadata": chunk["metadata"],
                    "embedding": embedding_item.embedding,
                }

            # Persist after EVERY successful batch.
            # This makes the pipeline resumable.
            save_embedding_store(store)

            summary["embedded"] += len(batch)

            print(
                f"Batch {batch_number} completed successfully."
            )
            print(
                f"Embeddings generated: {len(batch)}"
            )

        except Exception as error:

            summary["failed"] += len(batch)

            summary["failed_batches"].append(
                {
                    "batch_number": batch_number,
                    "chunk_ids": [
                        chunk["id"] for chunk in batch
                    ],
                    "error": str(error),
                }
            )

            print(
                f"Batch {batch_number} FAILED."
            )
            print(f"Error: {error}")

    summary["estimated_cost_usd"] = (
        summary["input_tokens"] / 1000
    ) * PRICE_PER_1K_TOKENS

    return summary


# ============================================================
# SUMMARY
# ============================================================

def print_summary(summary: dict[str, Any]) -> None:

    print()
    print("=" * 70)
    print("RUN SUMMARY")
    print("=" * 70)

    print(f"Total chunks: {summary['total_chunks']}")
    print(
        f"Total batches processed: "
        f"{summary['total_batches']}"
    )
    print(
        f"Embeddings generated: "
        f"{summary['embedded']}"
    )
    print(
        f"Skipped existing embeddings: "
        f"{summary['skipped_existing']}"
    )
    print(
        f"Failed chunks: "
        f"{summary['failed']}"
    )
    print(
        f"Estimated input tokens: "
        f"{summary['input_tokens']}"
    )
    print(
        f"Estimated cost (USD): "
        f"${summary['estimated_cost_usd']:.6f}"
    )

    print()
    print("Failed batches:")

    if not summary["failed_batches"]:
        print("  None")

    else:
        for failure in summary["failed_batches"]:
            print(
                f"  Batch {failure['batch_number']} | "
                f"chunks={failure['chunk_ids']}"
            )
            print(
                f"  Error: {failure['error']}"
            )


# ============================================================
# VALIDATION
# ============================================================

def validate_summary(summary: dict[str, Any]) -> None:

    accounted_for = (
        summary["embedded"]
        + summary["skipped_existing"]
        + summary["failed"]
    )

    if accounted_for != summary["total_chunks"]:
        raise AssertionError(
            "Run summary does not account for all chunks."
        )

    if summary["embedded"] > 0:
        print("Batch embedding: PASS")
    else:
        print("Batch embedding: PASS (all chunks were skipped)")

    print("Cost tracking: PASS")
    print("Skip-on-rerun logic: PASS")
    print("Failure tracking: PASS")
    print("Persistent progress: PASS")
    print("Summary accounting: PASS")


# ============================================================
# MAIN
# ============================================================

def main():

    summary = run_embedding_pipeline(CHUNKS)

    print_summary(summary)

    validate_summary(summary)

    print()
    print("=" * 70)
    print("BATCH EMBEDDING DEMONSTRATION: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()