import os

import requests
from dotenv import load_dotenv
from openai import OpenAI

from .config import GEMINI_API_KEY

load_dotenv()


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
)

COLLECTION_NAME = "traderule_rag_chunks"

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001",
)

EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)


# ---------------------------------------------------------------------
# Embedding client
# ---------------------------------------------------------------------

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=EMBEDDING_BASE_URL,
    timeout=60.0,
    max_retries=0,
)


# ---------------------------------------------------------------------
# Task 1 - Test queries
# ---------------------------------------------------------------------

TEST_QUERIES = [
    {
        "name": "customs_compliance",
        "query": (
            "How can an exporter verify "
            "shipment compliance requirements?"
        ),
        "expected_source": "customs_requirements.txt",
    },
    {
        "name": "export_license",
        "query": (
            "When does an exporter need "
            "an export license?"
        ),
        "expected_source": "license_rules.txt",
    },
    {
        "name": "shipping_documents",
        "query": (
            "What documents should be prepared "
            "for an international shipment?"
        ),
        "expected_source": "shipping_documents.md",
    },
]


# ---------------------------------------------------------------------
# Task 2 - Retrieval settings
# ---------------------------------------------------------------------

SETTINGS = [
    {
        "name": "baseline_k3",
        "k": 3,
        "min_score": 0.0,
        "metadata_filter": None,
    },
    {
        "name": "strict_k5_score072",
        "k": 5,
        "min_score": 0.72,
        "metadata_filter": None,
    },
]


# ---------------------------------------------------------------------
# Query embedding
# ---------------------------------------------------------------------

def embed_query(query: str) -> list[float]:
    """Embed a query using the same model as the document chunks."""

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )

    return response.data[0].embedding


# ---------------------------------------------------------------------
# Qdrant search
# ---------------------------------------------------------------------

def qdrant_search(
    query_vector: list[float],
    k: int,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """Run vector search against Qdrant."""

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

    if metadata_filter is not None:
        payload["filter"] = metadata_filter

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["result"]


# ---------------------------------------------------------------------
# Format Qdrant results
# ---------------------------------------------------------------------

def format_results(
    results: list[dict],
) -> list[dict]:

    formatted = []

    for rank, item in enumerate(
        results,
        start=1,
    ):

        payload = item.get(
            "payload",
            {},
        )

        formatted.append(
            {
                "rank": rank,
                "score": item["score"],
                "chunk_id": payload.get(
                    "chunk_id"
                ),
                "text": payload.get(
                    "text",
                    "",
                ),
                "metadata": payload.get(
                    "metadata",
                    {},
                ),
            }
        )

    return formatted


# ---------------------------------------------------------------------
# Evaluate one retrieval setting
# ---------------------------------------------------------------------

def evaluate_setting(
    setting: dict,
) -> list[dict]:

    rows = []

    for test in TEST_QUERIES:

        query = test["query"]

        query_vector = embed_query(query)

        raw_results = qdrant_search(
            query_vector=query_vector,
            k=setting["k"],
            metadata_filter=setting[
                "metadata_filter"
            ],
        )

        results = format_results(
            raw_results
        )

        # Apply minimum similarity threshold.
        kept = [
            result
            for result in results
            if result["score"] >= setting["min_score"]
        ]

        returned_sources = [
            result["metadata"].get(
                "source"
            )
            for result in kept
        ]

        expected_source = test[
            "expected_source"
        ]

        # Top-k hit:
        # expected source appears anywhere
        # in the retrieved results.
        hit = (
            expected_source
            in returned_sources
        )

        # Top-1 hit:
        top1_hit = (
            len(kept) > 0
            and kept[0]["metadata"].get(
                "source"
            ) == expected_source
        )

        rows.append(
            {
                "name": test["name"],
                "query": query,
                "expected_source": expected_source,
                "returned_sources": returned_sources,
                "results": kept,
                "hit": hit,
                "top1_hit": top1_hit,
            }
        )

    return rows


# ---------------------------------------------------------------------
# Calculate metrics
# ---------------------------------------------------------------------

def calculate_metrics(
    rows: list[dict],
) -> dict:

    total = len(rows)

    hits = sum(
        1
        for row in rows
        if row["hit"]
    )

    top1_hits = sum(
        1
        for row in rows
        if row["top1_hit"]
    )

    hit_rate = (
        hits / total
        if total
        else 0.0
    )

    top1_rate = (
        top1_hits / total
        if total
        else 0.0
    )

    return {
        "total_queries": total,
        "hits": hits,
        "hit_rate": hit_rate,
        "top1_hits": top1_hits,
        "top1_rate": top1_rate,
    }


# ---------------------------------------------------------------------
# Print detailed results
# ---------------------------------------------------------------------

def print_setting_results(
    setting: dict,
    rows: list[dict],
    metrics: dict,
) -> None:

    print()
    print("=" * 70)
    print(
        f"SETTING: {setting['name']}"
    )
    print("=" * 70)

    print(
        f"k = {setting['k']}"
    )

    print(
        f"Minimum score = "
        f"{setting['min_score']}"
    )

    for row in rows:

        print()
        print(
            f"Query: {row['query']}"
        )

        print(
            f"Expected source: "
            f"{row['expected_source']}"
        )

        print(
            f"Hit: {row['hit']}"
        )

        print(
            f"Top-1 hit: "
            f"{row['top1_hit']}"
        )

        print(
            "Returned sources:"
        )

        for result in row["results"]:

            metadata = result[
                "metadata"
            ]

            print(
                f"  Rank {result['rank']} | "
                f"Score {result['score']:.6f} | "
                f"Source "
                f"{metadata.get('source')}"
            )

            print(
                f"  Text: "
                f"{result['text']}"
            )

    print()
    print("-" * 70)

    print(
        f"Hits: "
        f"{metrics['hits']}/"
        f"{metrics['total_queries']}"
    )

    print(
        f"Hit rate: "
        f"{metrics['hit_rate']:.2%}"
    )

    print(
        f"Top-1 hits: "
        f"{metrics['top1_hits']}/"
        f"{metrics['total_queries']}"
    )

    print(
        f"Top-1 hit rate: "
        f"{metrics['top1_rate']:.2%}"
    )


# ---------------------------------------------------------------------
# Task 4 - Choose best setting
# ---------------------------------------------------------------------

def choose_best_setting(
    evaluated: list[dict],
) -> dict:

    # Prefer higher hit rate.
    # If tied, prefer higher top-1 rate.
    # If still tied, prefer smaller k.
    ranked = sorted(
        evaluated,
        key=lambda item: (
            item["metrics"]["hit_rate"],
            item["metrics"]["top1_rate"],
            -item["setting"]["k"],
        ),
        reverse=True,
    )

    return ranked[0]


# ---------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print("RETRIEVAL RELEVANCE TUNING")
    print("=" * 70)

    print(
        f"Qdrant URL: {QDRANT_URL}"
    )

    print(
        f"Collection: "
        f"{COLLECTION_NAME}"
    )

    print(
        f"Embedding model: "
        f"{EMBEDDING_MODEL}"
    )

    print(
        f"Test queries: "
        f"{len(TEST_QUERIES)}"
    )

    print(
        f"Compared settings: "
        f"{len(SETTINGS)}"
    )

    # -------------------------------------------------------------
    # Validate test queries
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("TEST QUERIES")
    print("=" * 70)

    for index, test in enumerate(
        TEST_QUERIES,
        start=1,
    ):

        print()
        print(
            f"{index}. {test['query']}"
        )

        print(
            f"Expected source: "
            f"{test['expected_source']}"
        )

    # -------------------------------------------------------------
    # Evaluate all settings
    # -------------------------------------------------------------

    evaluated = []

    for setting in SETTINGS:

        rows = evaluate_setting(
            setting
        )

        metrics = calculate_metrics(
            rows
        )

        print_setting_results(
            setting,
            rows,
            metrics,
        )

        evaluated.append(
            {
                "setting": setting,
                "rows": rows,
                "metrics": metrics,
            }
        )

    # -------------------------------------------------------------
    # Comparison summary
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("SETTING COMPARISON")
    print("=" * 70)

    for item in evaluated:

        setting = item["setting"]
        metrics = item["metrics"]

        print()
        print(
            f"Setting: "
            f"{setting['name']}"
        )

        print(
            f"k={setting['k']}, "
            f"min_score="
            f"{setting['min_score']}"
        )

        print(
            f"Hit rate: "
            f"{metrics['hit_rate']:.2%}"
        )

        print(
            f"Top-1 hit rate: "
            f"{metrics['top1_rate']:.2%}"
        )

    # -------------------------------------------------------------
    # Choose best setting
    # -------------------------------------------------------------

    best = choose_best_setting(
        evaluated
    )

    best_setting = best["setting"]
    best_metrics = best["metrics"]

    print()
    print("=" * 70)
    print("BEST SETTING")
    print("=" * 70)

    print(
        f"Selected: "
        f"{best_setting['name']}"
    )

    print(
        f"k = "
        f"{best_setting['k']}"
    )

    print(
        f"Minimum score = "
        f"{best_setting['min_score']}"
    )

    print(
        f"Hit rate = "
        f"{best_metrics['hit_rate']:.2%}"
    )

    print(
        f"Top-1 hit rate = "
        f"{best_metrics['top1_rate']:.2%}"
    )

    print()
    print("JUSTIFICATION")
    print("-" * 70)

    print(
        "The selected configuration has the "
        "best measured retrieval relevance "
        "on the test query set."
    )

    print(
        "The evaluation uses top-k hit rate "
        "and top-1 hit rate to determine whether "
        "the expected source was retrieved."
    )

    print()
    print("=" * 70)
    print("RETRIEVAL RELEVANCE TUNING: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()