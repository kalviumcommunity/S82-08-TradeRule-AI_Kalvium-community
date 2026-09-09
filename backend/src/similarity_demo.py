from math import sqrt

from openai import OpenAI

from .config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_BASE_URL,
)


# ------------------------------------------------------------
# EMBEDDING CLIENT
# ------------------------------------------------------------

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=EMBEDDING_BASE_URL,
    timeout=60.0,
    max_retries=0,
)


# ------------------------------------------------------------
# SAMPLE CHUNK RECORDS
# ------------------------------------------------------------

CHUNK_RECORDS = [
    {
        "text": (
            "International shipment compliance requires "
            "exporters to verify product classification "
            "and destination requirements."
        ),
        "metadata": {
            "source": "customs_requirements.txt",
            "chunk_index": 0,
            "section": "export compliance",
            "document_type": "txt",
        },
    },
    {
        "text": (
            "Exporters should verify export control "
            "requirements, destination restrictions, "
            "required licenses, and customs documentation."
        ),
        "metadata": {
            "source": "export_guidelines.md",
            "chunk_index": 0,
            "section": "export guidelines",
            "document_type": "markdown",
        },
    },
    {
        "text": (
            "Importers should verify customs documentation "
            "before the shipment arrives."
        ),
        "metadata": {
            "source": "import_rules.html",
            "chunk_index": 0,
            "section": "import requirements",
            "document_type": "html",
        },
    },
    {
        "text": (
            "The cafeteria menu includes pasta, rice, "
            "vegetables, and fresh fruit."
        ),
        "metadata": {
            "source": "campus-guide.txt",
            "chunk_index": 3,
            "section": "cafeteria",
            "document_type": "txt",
        },
    },
]


# ------------------------------------------------------------
# EMBEDDING FUNCTION
# ------------------------------------------------------------

def embed_text(
    text: str,
) -> list[float]:
    """
    Generate one embedding using the same model used
    for the document chunks.
    """

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text],
    )

    return response.data[0].embedding


# ------------------------------------------------------------
# COSINE SIMILARITY
# ------------------------------------------------------------

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two vectors.

    Cosine similarity compares the direction of vectors
    rather than their raw magnitude.
    """

    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Vectors must have the same dimension"
        )

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b,
        )
    )

    magnitude_a = sqrt(
        sum(
            value * value
            for value in vector_a
        )
    )

    magnitude_b = sqrt(
        sum(
            value * value
            for value in vector_b
        )
    )

    if magnitude_a == 0 or magnitude_b == 0:
        raise ValueError(
            "Cannot calculate similarity "
            "for a zero vector"
        )

    return (
        dot_product
        / (magnitude_a * magnitude_b)
    )


# ------------------------------------------------------------
# EMBED CHUNK RECORDS
# ------------------------------------------------------------

def embed_chunks(
    records: list[dict],
) -> list[dict]:
    """
    Generate and attach an embedding to every chunk record.
    """

    embedded_records = []

    for record in records:
        embedding = embed_text(
            record["text"]
        )

        embedded_records.append(
            {
                "text": record["text"],
                "metadata": record["metadata"],
                "embedding": embedding,
            }
        )

    return embedded_records


# ------------------------------------------------------------
# RANK CHUNKS
# ------------------------------------------------------------

def rank_chunks(
    query_embedding: list[float],
    records: list[dict],
) -> list[dict]:
    """
    Compare the query embedding against every chunk
    and return records sorted from highest to lowest
    similarity.
    """

    ranked = []

    for record in records:
        score = cosine_similarity(
            query_embedding,
            record["embedding"],
        )

        ranked.append(
            {
                **record,
                "score": score,
            }
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return ranked


# ------------------------------------------------------------
# PRINT RANKINGS
# ------------------------------------------------------------

def print_ranked_results(
    ranked: list[dict],
) -> None:
    """
    Print every chunk from most similar to least similar.
    """

    print("\n" + "=" * 70)
    print("RANKED CHUNK RESULTS")
    print("=" * 70)

    for rank, record in enumerate(
        ranked,
        start=1,
    ):
        print("\n" + "-" * 70)

        print(
            f"Rank {rank}"
        )

        print("-" * 70)

        print(
            f"Similarity score: "
            f"{record['score']:.6f}"
        )

        print(
            f"Source: "
            f"{record['metadata']['source']}"
        )

        print(
            f"Chunk index: "
            f"{record['metadata']['chunk_index']}"
        )

        print(
            f"Section: "
            f"{record['metadata']['section']}"
        )

        print(
            f"Document type: "
            f"{record['metadata']['document_type']}"
        )

        print(
            "\nText:"
        )

        print(
            record["text"]
        )


# ------------------------------------------------------------
# PRINT MOST / LEAST SIMILAR
# ------------------------------------------------------------

def print_extremes(
    ranked: list[dict],
) -> None:
    """
    Print the most and least similar chunks.
    """

    if not ranked:
        return

    most_similar = ranked[0]
    least_similar = ranked[-1]

    print("\n" + "=" * 70)
    print("MOST SIMILAR CHUNK")
    print("=" * 70)

    print(
        f"Score: "
        f"{most_similar['score']:.6f}"
    )

    print(
        f"Source: "
        f"{most_similar['metadata']['source']}"
    )

    print(
        f"Metadata: "
        f"{most_similar['metadata']}"
    )

    print(
        f"Text: "
        f"{most_similar['text']}"
    )

    print("\n" + "=" * 70)
    print("LEAST SIMILAR CHUNK")
    print("=" * 70)

    print(
        f"Score: "
        f"{least_similar['score']:.6f}"
    )

    print(
        f"Source: "
        f"{least_similar['metadata']['source']}"
    )

    print(
        f"Metadata: "
        f"{least_similar['metadata']}"
    )

    print(
        f"Text: "
        f"{least_similar['text']}"
    )


# ------------------------------------------------------------
# VALIDATION
# ------------------------------------------------------------

def validate_ranking(
    ranked: list[dict],
) -> bool:
    """
    Verify that the ranking is ordered from highest
    similarity to lowest similarity.
    """

    scores = [
        record["score"]
        for record in ranked
    ]

    is_sorted = all(
        scores[index]
        >= scores[index + 1]
        for index in range(
            len(scores) - 1
        )
    )

    if not is_sorted:
        raise AssertionError(
            "Similarity results are not correctly ranked"
        )

    return True


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main() -> None:

    print("=" * 70)
    print("EMBEDDING SIMILARITY & DISTANCE METRICS")
    print("=" * 70)

    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    query = (
        "How can an exporter verify shipment "
        "compliance requirements?"
    )

    print(
        f"\nQuery: "
        f"{query}"
    )

    print(
        f"Embedding model: "
        f"{EMBEDDING_MODEL}"
    )

    # --------------------------------------------------------
    # EMBED QUERY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("QUERY EMBEDDING")
    print("=" * 70)

    query_embedding = embed_text(
        query
    )

    print(
        f"Query vector length: "
        f"{len(query_embedding)}"
    )

    print(
        "Query embedding generated: PASS"
    )

    # --------------------------------------------------------
    # EMBED CHUNKS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("CHUNK EMBEDDINGS")
    print("=" * 70)

    embedded_records = embed_chunks(
        CHUNK_RECORDS
    )

    print(
        f"Chunks embedded: "
        f"{len(embedded_records)}"
    )

    print(
        f"Chunk vector length: "
        f"{len(embedded_records[0]['embedding'])}"
    )

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    ranked = rank_chunks(
        query_embedding,
        embedded_records,
    )

    # --------------------------------------------------------
    # PRINT RANKINGS
    # --------------------------------------------------------

    print_ranked_results(
        ranked
    )

    # --------------------------------------------------------
    # MOST / LEAST SIMILAR
    # --------------------------------------------------------

    print_extremes(
        ranked
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    ranking_valid = validate_ranking(
        ranked
    )

    print("\n" + "=" * 70)
    print("RANKING VALIDATION")
    print("=" * 70)

    print(
        f"Results sorted highest to lowest: "
        f"{ranking_valid}"
    )

    # --------------------------------------------------------
    # METRIC JUSTIFICATION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("METRIC JUSTIFICATION")
    print("=" * 70)

    print(
        """
Cosine similarity was chosen because it compares the
direction of embedding vectors.

For semantic embeddings, vector direction represents
meaning in the embedding space. A higher cosine similarity
indicates that the query and chunk are more closely related
in that space.

Similarity and distance express the same retrieval idea
from different perspectives:

- Similarity: higher score means more related.
- Distance: lower score means more related.

The ranking step sorts chunks by similarity so that the
most relevant chunks can be selected as context for the
RAG language model.
"""
    )

    # --------------------------------------------------------
    # RETRIEVAL EXPLANATION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("WHY RANKING POWERS RETRIEVAL")
    print("=" * 70)

    print(
        """
A RAG system embeds the user's query and compares it with
the stored embeddings of document chunks.

The chunks are ranked according to similarity.

The highest-ranked chunks become candidates for the top-k
retrieval set and can then be provided to the language model
as supporting context.

A high similarity score indicates semantic closeness, but
it does not guarantee that the chunk is factually correct,
complete, current, or safe to use by itself.
"""
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SIMILARITY DEMONSTRATION RESULT")
    print("=" * 70)

    print(
        "Cosine similarity calculation: PASS"
    )

    print(
        "Query compared against chunks: PASS"
    )

    print(
        "Similarity ranking: PASS"
    )

    print(
        "Most similar result shown: PASS"
    )

    print(
        "Least similar result shown: PASS"
    )

    print(
        "Metric justification: PASS"
    )

    print(
        "\nSIMILARITY RANKING DEMONSTRATION: PASS"
    )


if __name__ == "__main__":
    main()