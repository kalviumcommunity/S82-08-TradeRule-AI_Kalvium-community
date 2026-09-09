import logging

from openai import OpenAI

from .config import (
    GEMINI_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDING_BASE_URL,
)


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO
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
# SAMPLE PREPARED CHUNKS
# ------------------------------------------------------------

CHUNKS = [
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
]


# ------------------------------------------------------------
# GENERATE EMBEDDINGS
# ------------------------------------------------------------

def embed_chunks(
    chunks: list[dict],
) -> list[dict]:
    """
    Generate embeddings for prepared chunks using an
    OpenAI-compatible embeddings API.

    The returned record keeps:

        text
        metadata
        embedding

    together so retrieval can later identify the source
    text associated with each vector.
    """

    if not chunks:
        return []

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=texts,
    )

    records = []

    for chunk, item in zip(
        chunks,
        response.data,
    ):
        records.append(
            {
                "text": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": item.embedding,
            }
        )

    return records


# ------------------------------------------------------------
# VALIDATE EMBEDDING RECORDS
# ------------------------------------------------------------

def validate_records(
    records: list[dict],
) -> bool:
    """
    Validate that every embedding record contains
    text, metadata, and a non-empty vector.
    """

    if not records:
        raise AssertionError(
            "No embedding records were generated"
        )

    required_fields = {
        "text",
        "metadata",
        "embedding",
    }

    for index, record in enumerate(
        records
    ):
        if set(record.keys()) != required_fields:
            raise AssertionError(
                f"Record {index} has incorrect fields: "
                f"{set(record.keys())}"
            )

        if not record["text"]:
            raise AssertionError(
                f"Record {index} has empty source text"
            )

        if not record["metadata"]:
            raise AssertionError(
                f"Record {index} has missing metadata"
            )

        if not record["embedding"]:
            raise AssertionError(
                f"Record {index} has an empty embedding"
            )

    return True


# ------------------------------------------------------------
# VALIDATE VECTOR DIMENSIONS
# ------------------------------------------------------------

def validate_dimensions(
    records: list[dict],
) -> int:
    """
    Confirm that all embedding vectors have the same length.
    """

    dimensions = [
        len(record["embedding"])
        for record in records
    ]

    if not dimensions:
        raise AssertionError(
            "No vector dimensions available"
        )

    first_dimension = dimensions[0]

    if not all(
        dimension == first_dimension
        for dimension in dimensions
    ):
        raise AssertionError(
            f"Inconsistent vector dimensions: "
            f"{dimensions}"
        )

    return first_dimension


# ------------------------------------------------------------
# PRINT SAMPLE VECTOR
# ------------------------------------------------------------

def print_sample_vector(
    records: list[dict],
    values_to_show: int = 5,
) -> None:
    """
    Print one stored record with trimmed vector values.
    """

    record = records[0]

    print("\n" + "=" * 70)
    print("SAMPLE STORED EMBEDDING RECORD")
    print("=" * 70)

    print("\nSource text:")
    print(record["text"])

    print("\nMetadata:")

    for key, value in record[
        "metadata"
    ].items():
        print(
            f"  {key}: {value}"
        )

    print("\nVector length:")
    print(
        len(record["embedding"])
    )

    print(
        f"\nFirst {values_to_show} vector values:"
    )

    print(
        record["embedding"][
            :values_to_show
        ]
    )


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main() -> None:

    print("=" * 70)
    print("GENERATING EMBEDDINGS VIA API")
    print("=" * 70)

    print(
        f"\nEmbedding model: "
        f"{EMBEDDING_MODEL}"
    )

    print(
        f"Embedding base URL: "
        f"{EMBEDDING_BASE_URL}"
    )

    print(
        f"Prepared chunks: "
        f"{len(CHUNKS)}"
    )

    # --------------------------------------------------------
    # GENERATE EMBEDDINGS
    # --------------------------------------------------------

    records = embed_chunks(
        CHUNKS
    )

    print("\n" + "=" * 70)
    print("EMBEDDING API RESULT")
    print("=" * 70)

    print(
        f"Chunks embedded: "
        f"{len(records)}"
    )

    # --------------------------------------------------------
    # VALIDATE RECORD STRUCTURE
    # --------------------------------------------------------

    records_valid = validate_records(
        records
    )

    print(
        f"Text + metadata + vector stored together: "
        f"{records_valid}"
    )

    # --------------------------------------------------------
    # VALIDATE VECTOR DIMENSIONS
    # --------------------------------------------------------

    dimension = validate_dimensions(
        records
    )

    print(
        f"Vector length: "
        f"{dimension}"
    )

    # --------------------------------------------------------
    # PRINT SAMPLE RECORD
    # --------------------------------------------------------

    print_sample_vector(
        records
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("EMBEDDING API VALIDATION")
    print("=" * 70)

    print(
        "API embedding generation: PASS"
    )

    print(
        "Environment-based configuration: PASS"
    )

    print(
        "Source text preservation: PASS"
    )

    print(
        "Metadata preservation: PASS"
    )

    print(
        "Vector dimension validation: PASS"
    )

    print(
        "Sample vector output: PASS"
    )

    print(
        "\nEMBEDDING API DEMONSTRATION: PASS"
    )


if __name__ == "__main__":
    main()