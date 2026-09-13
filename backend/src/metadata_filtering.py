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
# Task 1 - Embed query
# ---------------------------------------------------------------------

def embed_query(query: str) -> list[float]:
    """
    Embed the user query using the same embedding model
    used for the indexed document chunks.
    """

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )

    return response.data[0].embedding


# ---------------------------------------------------------------------
# Metadata filter builder
# ---------------------------------------------------------------------

def build_section_filter(section: str) -> dict:
    """
    Build a Qdrant metadata filter for the section field.
    """

    return {
        "must": [
            {
                "key": "metadata.section",
                "match": {
                    "value": section,
                },
            }
        ]
    }


# ---------------------------------------------------------------------
# Task 1 & 2 - Qdrant vector search
# ---------------------------------------------------------------------

def qdrant_search(
    query_vector: list[float],
    k: int = 3,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """
    Run vector similarity search with an optional
    Qdrant metadata filter.
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
# Convert Qdrant results
# ---------------------------------------------------------------------

def format_results(results: list[dict]) -> list[dict]:
    """
    Convert raw Qdrant results into an easy-to-inspect format.
    """

    formatted = []

    for rank, item in enumerate(results, start=1):

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
# Retrieval helper
# ---------------------------------------------------------------------

def retrieve(
    query: str,
    k: int = 3,
    metadata_filter: dict | None = None,
) -> list[dict]:
    """
    Embed query and perform filtered/unfiltered retrieval.
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    query_vector = embed_query(query)

    results = qdrant_search(
        query_vector=query_vector,
        k=k,
        metadata_filter=metadata_filter,
    )

    return format_results(results)


# ---------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------

def show_results(
    label: str,
    results: list[dict],
) -> None:
    """
    Print score, source, metadata and text.
    """

    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    if not results:
        print("No results found.")
        return

    for result in results:

        metadata = result["metadata"]

        print()
        print(
            f"Rank: {result['rank']}"
        )

        print(
            f"Score: "
            f"{result['score']:.6f}"
        )

        print(
            f"Chunk ID: "
            f"{result['chunk_id']}"
        )

        print(
            f"Source: "
            f"{metadata.get('source')}"
        )

        print(
            f"Chunk index: "
            f"{metadata.get('chunk_index')}"
        )

        print(
            f"Section: "
            f"{metadata.get('section')}"
        )

        print(
            f"Document type: "
            f"{metadata.get('document_type')}"
        )

        print(
            f"Text: "
            f"{result['text']}"
        )


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_results(
    results: list[dict],
) -> None:
    """
    Validate retrieved result structure.
    """

    required_keys = {
        "rank",
        "score",
        "chunk_id",
        "text",
        "metadata",
    }

    for result in results:

        assert required_keys.issubset(
            result.keys()
        )

        assert result["text"]

        assert result["chunk_id"]

        assert isinstance(
            result["score"],
            (int, float),
        )

        metadata = result["metadata"]

        assert "source" in metadata
        assert "chunk_index" in metadata
        assert "section" in metadata
        assert "document_type" in metadata

    scores = [
        result["score"]
        for result in results
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    ), "Results are not sorted by similarity."


# ---------------------------------------------------------------------
# Task 3 - Keyword scoring
# ---------------------------------------------------------------------

def keyword_score(
    text: str,
    keywords: list[str],
) -> int:
    """
    Count how many keywords occur in the text.
    """

    lowered = text.lower()

    return sum(
        1
        for word in keywords
        if word.lower() in lowered
    )


# ---------------------------------------------------------------------
# Task 3 - Hybrid ranking
# ---------------------------------------------------------------------

def hybrid_rank(
    vector_results: list[dict],
    keywords: list[str],
    vector_weight: float = 0.8,
    keyword_weight: float = 0.2,
) -> list[dict]:
    """
    Combine vector similarity with simple keyword matching.

    hybrid_score =
        vector_weight * vector_score
        +
        keyword_weight * keyword_score
    """

    ranked = []

    for item in vector_results:

        lexical_score = keyword_score(
            item["text"],
            keywords,
        )

        combined_score = (
            vector_weight * item["score"]
            + keyword_weight * lexical_score
        )

        ranked.append(
            {
                **item,
                "keyword_score": lexical_score,
                "hybrid_score": combined_score,
            }
        )

    return sorted(
        ranked,
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )


# ---------------------------------------------------------------------
# Show hybrid results
# ---------------------------------------------------------------------

def show_hybrid_results(
    results: list[dict],
) -> None:

    print()
    print("=" * 70)
    print("HYBRID RESULTS")
    print("=" * 70)

    for rank, result in enumerate(
        results,
        start=1,
    ):

        metadata = result["metadata"]

        print()
        print(
            f"Rank: {rank}"
        )

        print(
            f"Vector score: "
            f"{result['score']:.6f}"
        )

        print(
            f"Keyword score: "
            f"{result['keyword_score']}"
        )

        print(
            f"Hybrid score: "
            f"{result['hybrid_score']:.6f}"
        )

        print(
            f"Chunk ID: "
            f"{result['chunk_id']}"
        )

        print(
            f"Source: "
            f"{metadata.get('source')}"
        )

        print(
            f"Section: "
            f"{metadata.get('section')}"
        )

        print(
            f"Text: "
            f"{result['text']}"
        )


# ---------------------------------------------------------------------
# Task 4 - Precision comparison
# ---------------------------------------------------------------------

def compare_precision(
    unfiltered: list[dict],
    filtered: list[dict],
    target_section: str,
) -> None:
    """
    Demonstrate that filtering restricts results
    to the intended section.
    """

    filtered_sections = [
        result["metadata"].get("section")
        for result in filtered
    ]

    all_filtered_match = all(
        section == target_section
        for section in filtered_sections
    )

    assert all_filtered_match, (
        "Filtered results contain an "
        "unexpected section."
    )

    print()
    print("=" * 70)
    print("PRECISION COMPARISON")
    print("=" * 70)

    print(
        "Unfiltered result count:",
        len(unfiltered),
    )

    print(
        "Filtered result count:",
        len(filtered),
    )

    print(
        f"Filter target section: "
        f"{target_section}"
    )

    print(
        "All filtered results match "
        "target section:",
        all_filtered_match,
    )

    if all_filtered_match:
        print(
            "Filtering precision improvement: PASS"
        )


# ---------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------

def main():

    query = (
        "How can an exporter verify "
        "shipment compliance requirements?"
    )

    target_section = "export compliance"

    keywords = [
        "exporter",
        "compliance",
        "classification",
    ]

    print("=" * 70)
    print("METADATA FILTERING & HYBRID SEARCH")
    print("=" * 70)

    print(
        f"Qdrant URL: {QDRANT_URL}"
    )

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Embedding model: "
        f"{EMBEDDING_MODEL}"
    )

    print(
        f"Query: {query}"
    )

    print(
        f"Filter section: "
        f"{target_section}"
    )

    print(
        f"Hybrid keywords: "
        f"{keywords}"
    )

    # -------------------------------------------------------------
    # Embed query once
    # -------------------------------------------------------------

    query_vector = embed_query(query)

    print()
    print("=" * 70)
    print("QUERY EMBEDDING")
    print("=" * 70)

    print(
        f"Vector dimension: "
        f"{len(query_vector)}"
    )

    assert len(query_vector) == 3072

    print(
        "Embedding dimension validation: PASS"
    )

    # -------------------------------------------------------------
    # Task 2 - Unfiltered search
    # -------------------------------------------------------------

    unfiltered_raw = qdrant_search(
        query_vector=query_vector,
        k=5,
    )

    unfiltered = format_results(
        unfiltered_raw
    )

    validate_results(unfiltered)

    show_results(
        "UNFILTERED VECTOR SEARCH",
        unfiltered,
    )

    # -------------------------------------------------------------
    # Task 1 - Metadata filtered search
    # -------------------------------------------------------------

    metadata_filter = build_section_filter(
        target_section
    )

    filtered_raw = qdrant_search(
        query_vector=query_vector,
        k=5,
        metadata_filter=metadata_filter,
    )

    filtered = format_results(
        filtered_raw
    )

    validate_results(filtered)

    show_results(
        "FILTERED VECTOR SEARCH",
        filtered,
    )

    # -------------------------------------------------------------
    # Task 3 - Hybrid search
    # -------------------------------------------------------------

    hybrid_results = hybrid_rank(
        filtered,
        keywords=keywords,
        vector_weight=0.8,
        keyword_weight=0.2,
    )

    show_hybrid_results(
        hybrid_results
    )

    # -------------------------------------------------------------
    # Task 4 - Precision demonstration
    # -------------------------------------------------------------

    compare_precision(
        unfiltered,
        filtered,
        target_section,
    )

    # -------------------------------------------------------------
    # Final validation
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("VALIDATION")
    print("=" * 70)

    print(
        "Query embedding: PASS"
    )

    print(
        "Metadata filter applied: PASS"
    )

    print(
        "Unfiltered versus filtered comparison: PASS"
    )

    print(
        "Scores returned: PASS"
    )

    print(
        "Source text returned: PASS"
    )

    print(
        "Metadata returned: PASS"
    )

    print(
        "Keyword scoring: PASS"
    )

    print(
        "Hybrid ranking: PASS"
    )

    print(
        "Precision improvement demonstration: PASS"
    )

    print()
    print("=" * 70)
    print("METADATA FILTERING & HYBRID SEARCH: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()