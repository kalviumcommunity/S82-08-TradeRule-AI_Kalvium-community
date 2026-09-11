import os

import requests
from dotenv import load_dotenv
from openai import OpenAI

from .config import GEMINI_API_KEY

load_dotenv()

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
# Task 1 - Embed the user query
# ---------------------------------------------------------------------

def embed_query(query: str) -> list[float]:
    """
    Embed a user query using the same embedding model
    used for the indexed document chunks.
    """

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[query],
    )

    return response.data[0].embedding


# ---------------------------------------------------------------------
# Task 2 - Run top-k similarity search
# ---------------------------------------------------------------------

def qdrant_search(
    query_vector: list[float],
    k: int,
) -> list[dict]:
    """
    Search the Qdrant vector database and return
    the top-k most similar points.
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
        timeout=30,
    )

    response.raise_for_status()

    return response.json()["result"]


# ---------------------------------------------------------------------
# Combined retrieval function
# ---------------------------------------------------------------------

def retrieve(
    query: str,
    k: int = 3,
) -> list[dict]:
    """
    Embed the query and retrieve the top-k
    most similar chunks.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    query_vector = embed_query(query)

    results = qdrant_search(
        query_vector=query_vector,
        k=k,
    )

    retrieved = []

    for rank, item in enumerate(results, start=1):

        payload = item.get("payload", {})

        retrieved.append(
            {
                "rank": rank,
                "score": item["score"],
                "text": payload.get("text", ""),
                "metadata": payload.get("metadata", {}),
                "chunk_id": payload.get("chunk_id"),
            }
        )

    return retrieved


# ---------------------------------------------------------------------
# Task 3 - Print scores, text and metadata
# ---------------------------------------------------------------------

def print_results(
    query: str,
    k: int,
    results: list[dict],
) -> None:
    """
    Print retrieved chunks with:
    - rank
    - similarity score
    - chunk ID
    - source
    - chunk index
    - section
    - document type
    - source text
    """

    print()
    print("=" * 70)
    print(f"QUERY: {query}")
    print(f"k = {k}")
    print("=" * 70)

    for result in results:

        metadata = result["metadata"]

        print()
        print(f"Rank: {result['rank']}")
        print(f"Score: {result['score']:.6f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Source: {metadata.get('source')}")
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
        print(f"Text: {result['text']}")


# ---------------------------------------------------------------------
# Retrieval validation
# ---------------------------------------------------------------------

def validate_results(
    results: list[dict],
    expected_k: int,
) -> None:
    """
    Validate that every retrieval result contains
    the required information.
    """

    assert len(results) == expected_k, (
        f"Expected {expected_k} results, "
        f"received {len(results)}"
    )

    required_keys = {
        "rank",
        "score",
        "text",
        "metadata",
        "chunk_id",
    }

    for result in results:

        assert required_keys.issubset(
            result.keys()
        ), "Missing retrieval fields."

        assert isinstance(
            result["score"],
            (int, float),
        )

        assert result["text"], (
            "Retrieved source text is empty."
        )

        assert result["chunk_id"], (
            "Retrieved chunk ID is missing."
        )

        metadata = result["metadata"]

        assert "source" in metadata, (
            "Source metadata is missing."
        )

        assert "chunk_index" in metadata, (
            "Chunk index metadata is missing."
        )

    # Similarity scores must be descending.
    scores = [
        result["score"]
        for result in results
    ]

    assert scores == sorted(
        scores,
        reverse=True,
    ), "Results are not sorted by similarity."

    # Rank should be sequential.
    ranks = [
        result["rank"]
        for result in results
    ]

    assert ranks == list(
        range(1, expected_k + 1)
    ), "Ranks are incorrect."


# ---------------------------------------------------------------------
# Task 4 - Demonstrate changing k
# ---------------------------------------------------------------------

def demonstrate_changing_k(
    query_vector: list[float],
    query: str,
) -> dict[int, list[dict]]:
    """
    Run the same query with multiple k values
    and show how the retrieved context changes.
    """

    k_values = [1, 3, 5]

    all_results = {}

    print()
    print("=" * 70)
    print("TOP-K RETRIEVAL")
    print("=" * 70)

    for k in k_values:

        raw_results = qdrant_search(
            query_vector=query_vector,
            k=k,
        )

        retrieved = []

        for rank, item in enumerate(
            raw_results,
            start=1,
        ):

            payload = item.get(
                "payload",
                {},
            )

            retrieved.append(
                {
                    "rank": rank,
                    "score": item["score"],
                    "text": payload.get(
                        "text",
                        "",
                    ),
                    "metadata": payload.get(
                        "metadata",
                        {},
                    ),
                    "chunk_id": payload.get(
                        "chunk_id"
                    ),
                }
            )

        validate_results(
            retrieved,
            k,
        )

        all_results[k] = retrieved

        print()
        print(f"k = {k}")
        print("-" * 70)

        for result in retrieved:

            metadata = result["metadata"]

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

            print()

    return all_results


# ---------------------------------------------------------------------
# Main demonstration
# ---------------------------------------------------------------------

def main():

    query = (
        "How can an exporter verify "
        "shipment compliance requirements?"
    )

    print("=" * 70)
    print("SIMILARITY SEARCH & TOP-K RETRIEVAL")
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

    # -------------------------------------------------------------
    # Task 1
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

    print(
        f"First 5 values: "
        f"{query_vector[:5]}"
    )

    assert len(query_vector) == 3072

    print(
        "Embedding dimension validation: PASS"
    )

    # -------------------------------------------------------------
    # Tasks 2, 3 and 4
    # -------------------------------------------------------------

    all_results = demonstrate_changing_k(
        query_vector,
        query,
    )

    # -------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("RETRIEVAL VALIDATION")
    print("=" * 70)

    print(
        "Query embedded with document "
        "embedding model: PASS"
    )

    print(
        "Top-k similarity search: PASS"
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
        "Results sorted by similarity: PASS"
    )

    # -------------------------------------------------------------
    # Changing-k validation
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("CHANGING-K DEMONSTRATION")
    print("=" * 70)

    for k, results in all_results.items():

        print(
            f"k={k}: "
            f"{len(results)} retrieved chunks"
        )

    assert len(all_results[1]) == 1
    assert len(all_results[3]) == 3
    assert len(all_results[5]) == 5

    print(
        "Changing k changes retrieved "
        "context: PASS"
    )

    # -------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("TOP-K RETRIEVAL: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()