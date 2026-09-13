"""
3.36 Retrieval Evaluation & Recall Testing

Evaluates the quality of the TradeRule AI retriever using a
labelled query set.

Metrics:
- Recall@5
- Precision@5

The script:
1. Embeds each labelled query.
2. Retrieves top-k chunks from Qdrant.
3. Compares retrieved chunk IDs with labelled relevant IDs.
4. Calculates recall and precision.
5. Reports failures and likely causes.
6. Saves/prints a summary suitable for assignment evidence.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333").rstrip("/")
COLLECTION_NAME = "traderule_rag_chunks"

EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

TOP_K = 5


# -------------------------------------------------------------------
# Labelled evaluation dataset
# -------------------------------------------------------------------
#
# Each query is mapped to the chunk(s) that should contain the
# information required to answer that query.
#
# These IDs correspond to the stable chunk IDs already used during
# the TradeRule AI embedding/indexing stages.
# -------------------------------------------------------------------

LABELLED_QUERIES = [
    {
        "name": "customs_compliance",
        "query": "How can an exporter verify shipment compliance requirements?",
        "relevant_chunk_ids": {
            "customs-0",
        },
        "expected_sources": {
            "customs_requirements.txt",
        },
    },
    {
        "name": "export_license",
        "query": "When does an exporter need an export license?",
        "relevant_chunk_ids": {
            "license-0",
        },
        "expected_sources": {
            "license_rules.txt",
        },
    },
    {
        "name": "shipping_documents",
        "query": "What documents should be prepared for an international shipment?",
        "relevant_chunk_ids": {
            "documentation-0",
        },
        "expected_sources": {
            "shipping_documents.md",
        },
    },
    {
        "name": "export_requirements",
        "query": "What export control and destination requirements should exporters verify?",
        "relevant_chunk_ids": {
            "export-0",
        },
        "expected_sources": {
            "export_guidelines.md",
        },
    },
    {
        "name": "import_requirements",
        "query": "What customs documentation should an importer verify before shipment arrival?",
        "relevant_chunk_ids": {
            "import-0",
        },
        "expected_sources": {
            "import_rules.html",
        },
    },
]


# -------------------------------------------------------------------
# Validation helpers
# -------------------------------------------------------------------

def validate_configuration() -> None:
    """Validate required environment configuration."""

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check your backend/.env configuration."
        )

    print("Configuration")
    print("-" * 70)
    print(f"Qdrant URL       : {QDRANT_URL}")
    print(f"Collection       : {COLLECTION_NAME}")
    print(f"Embedding model  : {EMBEDDING_MODEL}")
    print(f"Embedding API    : {EMBEDDING_BASE_URL}")
    print(f"Top-K            : {TOP_K}")
    print(f"Labelled queries : {len(LABELLED_QUERIES)}")
    print()


def validate_collection() -> None:
    """Check that the Qdrant collection exists."""

    url = f"{QDRANT_URL}/collections/{COLLECTION_NAME}"

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(
            f"Qdrant collection '{COLLECTION_NAME}' was not found.\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

    collection = response.json().get("result", {})

    vector_config = collection.get("config", {}).get(
        "params", {}
    ).get("vectors", {})

    print("Qdrant collection validation")
    print("-" * 70)

    print(f"Collection exists: {COLLECTION_NAME}")

    if isinstance(vector_config, dict):
        size = vector_config.get("size")
        distance = vector_config.get("distance")

        if size:
            print(f"Vector dimension : {size}")

        if distance:
            print(f"Distance         : {distance}")

    print()


# -------------------------------------------------------------------
# Embedding client
# -------------------------------------------------------------------

def create_embedding_client() -> OpenAI:
    """Create the OpenAI-compatible Gemini client."""

    return OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )


def embed_query(
    client: OpenAI,
    query: str,
) -> list[float]:
    """Generate an embedding for the query."""

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )

    return response.data[0].embedding


# -------------------------------------------------------------------
# Qdrant retrieval
# -------------------------------------------------------------------

def retrieve(
    query_vector: list[float],
    k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Retrieve top-k chunks from Qdrant using vector similarity.
    """

    url = (
        f"{QDRANT_URL}/collections/"
        f"{COLLECTION_NAME}/points/search"
    )

    payload = {
        "vector": query_vector,
        "limit": k,
        "with_payload": True,
        "with_vector": False,
    }

    response = requests.post(
        url,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Qdrant search failed.\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

    result = response.json().get("result", [])

    return result


# -------------------------------------------------------------------
# Result extraction
# -------------------------------------------------------------------

def extract_chunk_id(result: dict[str, Any]) -> str | None:
    """
    Extract the stable application chunk ID from the Qdrant payload.
    """

    payload = result.get("payload") or {}

    chunk_id = payload.get("chunk_id")

    if chunk_id:
        return str(chunk_id)

    return None


def extract_source(result: dict[str, Any]) -> str:
    """Extract source filename from metadata."""

    payload = result.get("payload") or {}

    metadata = payload.get("metadata") or {}

    source = metadata.get("source")

    if source:
        return str(source)

    # Fallback if metadata is flattened.
    source = payload.get("source")

    if source:
        return str(source)

    return "unknown"


def extract_text(result: dict[str, Any]) -> str:
    """Extract chunk text."""

    payload = result.get("payload") or {}

    text = payload.get("text")

    if text:
        return str(text)

    return ""


# -------------------------------------------------------------------
# Query evaluation
# -------------------------------------------------------------------

def evaluate_query(
    client: OpenAI,
    item: dict[str, Any],
    k: int = TOP_K,
) -> dict[str, Any]:
    """
    Evaluate one labelled query.

    Recall@k:
        relevant chunks retrieved / total relevant chunks

    Precision@k:
        relevant chunks retrieved / total retrieved chunks
    """

    query = item["query"]
    relevant_ids = set(item["relevant_chunk_ids"])

    query_vector = embed_query(
        client,
        query,
    )

    results = retrieve(
        query_vector,
        k=k,
    )

    retrieved_ids = []

    result_rows = []

    for rank, result in enumerate(results, start=1):
        chunk_id = extract_chunk_id(result)

        if chunk_id is None:
            chunk_id = f"unknown-{rank}"

        retrieved_ids.append(chunk_id)

        result_rows.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "score": float(result.get("score", 0.0)),
                "source": extract_source(result),
                "text": extract_text(result),
            }
        )

    retrieved_set = set(retrieved_ids)

    hits = sorted(
        relevant_ids.intersection(retrieved_set)
    )

    recall = (
        len(hits) / len(relevant_ids)
        if relevant_ids
        else 0.0
    )

    precision = (
        len(hits) / len(retrieved_ids)
        if retrieved_ids
        else 0.0
    )

    expected_rank = None

    for row in result_rows:
        if row["chunk_id"] in relevant_ids:
            expected_rank = row["rank"]
            break

    return {
        "name": item["name"],
        "query": query,
        "relevant_chunk_ids": sorted(relevant_ids),
        "expected_sources": sorted(item.get("expected_sources", set())),
        "retrieved_ids": retrieved_ids,
        "hits": hits,
        "recall": recall,
        "precision": precision,
        "expected_rank": expected_rank,
        "results": result_rows,
    }


# -------------------------------------------------------------------
# Failure analysis
# -------------------------------------------------------------------

def identify_failure_cause(
    row: dict[str, Any],
) -> str:
    """
    Provide a reasonable likely cause for a failed query.

    This is an interpretation of the retrieval result, not a
    machine-generated ground-truth diagnosis.
    """

    if row["recall"] >= 1.0:
        return "No retrieval failure."

    if row["expected_rank"] is None:
        return (
            "The relevant chunk was not present in the top-k results. "
            "Possible causes include query wording mismatch, semantic "
            "similarity weakness, noisy chunks, or insufficient k."
        )

    return (
        "The relevant chunk was retrieved but ranked below the "
        "preferred position. Possible causes include semantic "
        "overlap with competing chunks, broad query wording, "
        "or insufficient ranking precision."
    )


# -------------------------------------------------------------------
# Reporting
# -------------------------------------------------------------------

def print_query_report(
    row: dict[str, Any],
) -> None:
    """Print detailed results for one query."""

    print("=" * 80)
    print(f"QUERY: {row['name']}")
    print("=" * 80)

    print(f"Query:")
    print(f"  {row['query']}")
    print()

    print("Expected relevant chunk IDs:")
    print(f"  {row['relevant_chunk_ids']}")
    print()

    print("Retrieved chunk IDs:")
    print(f"  {row['retrieved_ids']}")
    print()

    print("Hits:")
    print(f"  {row['hits']}")
    print()

    print(f"Expected chunk rank:")
    print(f"  {row['expected_rank']}")
    print()

    print(f"Recall@{TOP_K}:")
    print(f"  {row['recall']:.3f}")
    print()

    print(f"Precision@{TOP_K}:")
    print(f"  {row['precision']:.3f}")
    print()

    print("Retrieved candidates:")

    for result in row["results"]:
        print(
            f"  {result['rank']}. "
            f"{result['chunk_id']} | "
            f"{result['source']} | "
            f"score={result['score']:.6f}"
        )

    print()

    print("Failure analysis:")
    print(f"  {identify_failure_cause(row)}")
    print()


def print_summary(
    rows: list[dict[str, Any]],
) -> None:
    """Print aggregate evaluation metrics."""

    if not rows:
        print("No evaluation rows.")
        return

    average_recall = sum(
        row["recall"] for row in rows
    ) / len(rows)

    average_precision = sum(
        row["precision"] for row in rows
    ) / len(rows)

    failures = [
        row
        for row in rows
        if row["recall"] < 1.0
    ]

    print("=" * 80)
    print("FINAL RETRIEVAL EVALUATION SUMMARY")
    print("=" * 80)

    print(f"Queries evaluated : {len(rows)}")
    print(f"Top-K             : {TOP_K}")
    print(
        f"Average Recall@{TOP_K}    : "
        f"{average_recall:.3f}"
    )
    print(
        f"Average Precision@{TOP_K} : "
        f"{average_precision:.3f}"
    )
    print(f"Failures          : {len(failures)}")
    print()

    if failures:
        print("FAILED QUERIES")
        print("-" * 80)

        for failure in failures:
            print(f"Query : {failure['query']}")
            print(
                f"Expected : "
                f"{failure['relevant_chunk_ids']}"
            )
            print(
                f"Retrieved : "
                f"{failure['retrieved_ids']}"
            )
            print(
                f"Likely cause : "
                f"{identify_failure_cause(failure)}"
            )
            print()
    else:
        print(
            "No retrieval failures were observed in the "
            "labelled evaluation set."
        )

        print()
        print(
            "Interpretation: the current retriever successfully "
            "retrieved every labelled relevant chunk within the "
            f"top-{TOP_K} results."
        )

        print()
        print(
            "Limitation: this evaluation uses a small sample corpus. "
            "A larger and more diverse labelled query set would "
            "provide stronger evidence of retrieval quality."
        )

    print()


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> None:
    """Run the complete retrieval evaluation."""

    print()
    print("=" * 80)
    print("3.36 RETRIEVAL EVALUATION & RECALL TESTING")
    print("=" * 80)
    print()

    validate_configuration()
    validate_collection()

    client = create_embedding_client()

    rows = []

    for index, item in enumerate(
        LABELLED_QUERIES,
        start=1,
    ):
        print(
            f"Evaluating query {index}/"
            f"{len(LABELLED_QUERIES)}..."
        )

        row = evaluate_query(
            client,
            item,
            k=TOP_K,
        )

        rows.append(row)

    print()

    for row in rows:
        print_query_report(row)

    print_summary(rows)

    print("=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)
    print()


if __name__ == "__main__":
    main()