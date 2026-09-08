import logging
from math import sqrt

from google import genai

from .config import GEMINI_API_KEY


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

EMBED_MODEL = "gemini-embedding-001"

logging.basicConfig(
    level=logging.INFO
)

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ------------------------------------------------------------
# EMBEDDING GENERATION
# ------------------------------------------------------------

def embed(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a list of texts.

    Each text is converted into a numeric vector representing
    semantic information about that text.
    """

    embeddings = []

    for text in texts:
        response = client.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
        )

        embedding = response.embeddings[0].values

        embeddings.append(
            list(embedding)
        )

    return embeddings


# ------------------------------------------------------------
# COSINE SIMILARITY
# ------------------------------------------------------------

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two vectors.

    Cosine similarity compares the direction of vectors.

    A higher value means the vectors are more similar in
    semantic space.
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
# VECTOR VALIDATION
# ------------------------------------------------------------

def validate_dimensions(
    embeddings: list[list[float]],
) -> int:
    """
    Verify that every embedding has the same dimension.
    """

    if not embeddings:
        raise ValueError(
            "No embeddings were generated"
        )

    dimensions = [
        len(vector)
        for vector in embeddings
    ]

    first_dimension = dimensions[0]

    all_same = all(
        dimension == first_dimension
        for dimension in dimensions
    )

    if not all_same:
        raise AssertionError(
            f"Embedding dimensions are inconsistent: "
            f"{dimensions}"
        )

    print(
        f"All vectors have the same dimension: "
        f"{all_same}"
    )

    return first_dimension


# ------------------------------------------------------------
# PRINT VECTOR SAMPLE
# ------------------------------------------------------------

def print_vector_sample(
    vector: list[float],
    count: int = 8,
) -> None:
    """
    Print only the first few vector values so the output
    remains readable.
    """

    print(
        f"First {count} vector values:"
    )

    print(
        vector[:count]
    )


# ------------------------------------------------------------
# MAIN DEMONSTRATION
# ------------------------------------------------------------

def main() -> None:

    print("=" * 70)
    print("EMBEDDINGS FUNDAMENTALS & VECTOR REPRESENTATION")
    print("=" * 70)

    # --------------------------------------------------------
    # SAMPLE TEXTS
    # --------------------------------------------------------

    texts = [
        "How do I reset my account password?",
        "What are the steps to recover access to my login?",
        "The cafeteria menu has pasta today.",
    ]

    print("\nSample texts:")

    for index, text in enumerate(
        texts,
        start=1,
    ):
        print(
            f"{index}. {text}"
        )

    # --------------------------------------------------------
    # GENERATE EMBEDDINGS
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("GENERATING EMBEDDINGS")
    print("=" * 70)

    embeddings = embed(
        texts
    )

    print(
        f"\nGenerated embeddings: "
        f"{len(embeddings)}"
    )

    # --------------------------------------------------------
    # VECTOR DIMENSION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("VECTOR DIMENSION")
    print("=" * 70)

    dimension = validate_dimensions(
        embeddings
    )

    print(
        f"Embedding model: "
        f"{EMBED_MODEL}"
    )

    print(
        f"Vector dimension: "
        f"{dimension}"
    )

    for index, vector in enumerate(
        embeddings,
        start=1,
    ):
        print(
            f"Text {index}: "
            f"{len(vector)} dimensions"
        )

    # --------------------------------------------------------
    # SAMPLE VECTOR
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SAMPLE VECTOR")
    print("=" * 70)

    print(
        "\nText 1:"
    )

    print(
        texts[0]
    )

    print_vector_sample(
        embeddings[0]
    )

    # --------------------------------------------------------
    # COSINE SIMILARITY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("COSINE SIMILARITY")
    print("=" * 70)

    similar_score = cosine_similarity(
        embeddings[0],
        embeddings[1],
    )

    dissimilar_score = cosine_similarity(
        embeddings[0],
        embeddings[2],
    )

    print(
        "\nSimilar pair:"
    )

    print(
        f'"{texts[0]}"'
    )

    print(
        f'"{texts[1]}"'
    )

    print(
        f"Password vs login recovery: "
        f"{similar_score:.6f}"
    )

    print(
        "\nDissimilar pair:"
    )

    print(
        f'"{texts[0]}"'
    )

    print(
        f'"{texts[2]}"'
    )

    print(
        f"Password vs cafeteria menu: "
        f"{dissimilar_score:.6f}"
    )

    # --------------------------------------------------------
    # RANKING VALIDATION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SIMILARITY VALIDATION")
    print("=" * 70)

    print(
        f"Similar pair score: "
        f"{similar_score:.6f}"
    )

    print(
        f"Dissimilar pair score: "
        f"{dissimilar_score:.6f}"
    )

    ranking_is_correct = (
        similar_score > dissimilar_score
    )

    print(
        f"Similar pair scores higher: "
        f"{ranking_is_correct}"
    )

    if not ranking_is_correct:
        raise AssertionError(
            "The similar pair did not score "
            "higher than the dissimilar pair."
        )

    # --------------------------------------------------------
    # CONCEPT EXPLANATION
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("WHAT EMBEDDING VECTORS REPRESENT")
    print("=" * 70)

    print(
        """
Embedding vectors are numeric representations of the
meaning and semantic characteristics of text.

They are not random IDs and they are not simple keyword
counts. The embedding model converts text into a position
in a high-dimensional vector space.

Texts with similar meanings tend to have vectors that are
closer together, while unrelated texts tend to be farther
apart.

This allows a RAG system to search by semantic meaning
instead of requiring an exact keyword match.
"""
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print("=" * 70)
    print("EMBEDDING DEMONSTRATION RESULT")
    print("=" * 70)

    print(
        "Embedding generation: PASS"
    )

    print(
        "Vector dimension validation: PASS"
    )

    print(
        "Sample vector output: PASS"
    )

    print(
        "Cosine similarity calculation: PASS"
    )

    print(
        "Similar-vs-dissimilar ranking: PASS"
    )

    print(
        "Embedding explanation: PASS"
    )

    print(
        "\nEMBEDDING DEMONSTRATION: PASS"
    )


if __name__ == "__main__":
    main()