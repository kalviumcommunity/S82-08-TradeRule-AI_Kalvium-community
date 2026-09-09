from openai import OpenAI

from .config import (
    GEMINI_API_KEY,
    EMBEDDING_BASE_URL,
    EMBEDDING_MODEL,
)
from .similarity_demo import cosine_similarity


client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url=EMBEDDING_BASE_URL,
    timeout=60.0,
    max_retries=0,
)


# ============================================================
# TEST CORPUS
# ============================================================

CHUNK_RECORDS = [
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
# KNOWN RELEVANCE TEST CASES
# ============================================================

TEST_CASES = [
    {
        "name": "Exporter compliance",
        "query": (
            "How can an exporter verify shipment compliance requirements?"
        ),
        "expected_source": "customs_requirements.txt",
    },
    {
        "name": "Export licensing",
        "query": (
            "What export licenses and destination restrictions should I check?"
        ),
        "expected_source": "export_guidelines.md",
    },
    {
        "name": "Import customs documents",
        "query": (
            "What customs documents should be verified before an import shipment arrives?"
        ),
        "expected_source": "import_rules.html",
    },
    {
        "name": "Cafeteria information",
        "query": (
            "What food is available in the cafeteria?"
        ),
        "expected_source": "campus-guide.txt",
    },
]


# ============================================================
# EMBEDDING
# ============================================================

def embed_text(text: str) -> list[float]:
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text],
    )

    if not response.data:
        raise ValueError("Embedding API returned no vector.")

    return response.data[0].embedding


def embed_chunks(records):
    embedded = []

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[record["text"] for record in records],
    )

    if len(response.data) != len(records):
        raise ValueError(
            "Embedding count mismatch: "
            f"expected {len(records)}, got {len(response.data)}"
        )

    for record, embedding_item in zip(records, response.data):
        embedded.append(
            {
                **record,
                "embedding": embedding_item.embedding,
            }
        )

    return embedded


# ============================================================
# RANKING
# ============================================================

def rank_chunks(query_embedding, chunk_records):
    ranked = []

    for chunk in chunk_records:
        score = cosine_similarity(
            query_embedding,
            chunk["embedding"],
        )

        ranked.append(
            {
                **chunk,
                "score": score,
            }
        )

    return sorted(
        ranked,
        key=lambda item: item["score"],
        reverse=True,
    )


# ============================================================
# SINGLE TEST CASE
# ============================================================

def run_test_case(case, embedded_chunks):

    query_embedding = embed_text(case["query"])

    ranked = rank_chunks(
        query_embedding,
        embedded_chunks,
    )

    top = ranked[0]

    expected_matches_top = (
        top["metadata"]["source"]
        == case["expected_source"]
    )

    expected_position = next(
        (
            index + 1
            for index, item in enumerate(ranked)
            if item["metadata"]["source"]
            == case["expected_source"]
        ),
        None,
    )

    expected_item = next(
        (
            item
            for item in ranked
            if item["metadata"]["source"]
            == case["expected_source"]
        ),
        None,
    )

    expected_score = (
        expected_item["score"]
        if expected_item
        else None
    )

    return {
        "name": case["name"],
        "query": case["query"],
        "expected_source": case["expected_source"],
        "top_source": top["metadata"]["source"],
        "top_score": top["score"],
        "expected_position": expected_position,
        "expected_score": expected_score,
        "passed": expected_matches_top,
        "ranked": ranked,
    }


# ============================================================
# PRINT TEST RESULT
# ============================================================

def print_test_result(result):

    print()
    print("=" * 70)
    print(result["name"])
    print("=" * 70)

    print(f"Query: {result['query']}")
    print(f"Expected source: {result['expected_source']}")
    print(
        f"Top source: {result['top_source']}"
    )
    print(
        f"Top score: {result['top_score']:.6f}"
    )
    print(
        f"Expected source position: "
        f"{result['expected_position']}"
    )

    if result["expected_score"] is not None:
        print(
            f"Expected source score: "
            f"{result['expected_score']:.6f}"
        )

    print()
    print("Ranking:")

    for index, item in enumerate(
        result["ranked"],
        start=1,
    ):
        print(
            f"  {index}. "
            f"{item['metadata']['source']} "
            f"score={item['score']:.6f}"
        )

    print()
    print(
        f"Known relevance test: "
        f"{'PASS' if result['passed'] else 'FAIL'}"
    )


# ============================================================
# SANITY ANALYSIS
# ============================================================

def identify_surprising_cases(results):

    surprising = []

    for result in results:

        if not result["passed"]:
            surprising.append(
                {
                    "type": "failing case",
                    "name": result["name"],
                    "explanation": (
                        "The expected relevant source was not ranked first. "
                        "This shows that semantic similarity does not guarantee "
                        "exact retrieval relevance."
                    ),
                }
            )

        elif result["expected_position"] != 1:
            surprising.append(
                {
                    "type": "borderline case",
                    "name": result["name"],
                    "explanation": (
                        "The expected relevant source was present in the ranking "
                        "but was not the top result. Related vocabulary from other "
                        "documents may have produced a stronger semantic match."
                    ),
                }
            )

    # If every known case passes at rank 1, report a deliberate
    # corpus-level observation instead of fabricating a failure.
    if not surprising:
        surprising.append(
            {
                "type": "pipeline observation",
                "name": "Similarity limitation",
                "explanation": (
                    "All known relevance cases passed, but this does not prove "
                    "retrieval is always correct. The test corpus is small and "
                    "contains short synthetic documents. A larger corpus with "
                    "ambiguous queries could still produce ranking errors."
                ),
            }
        )

    return surprising


# ============================================================
# VALIDATION
# ============================================================

def validate_embeddings(embedded_chunks):

    if len(embedded_chunks) != len(CHUNK_RECORDS):
        raise AssertionError(
            "Not all chunks received embeddings."
        )

    dimensions = {
        len(chunk["embedding"])
        for chunk in embedded_chunks
    }

    if len(dimensions) != 1:
        raise AssertionError(
            f"Inconsistent embedding dimensions: {dimensions}"
        )

    dimension = next(iter(dimensions))

    if dimension <= 0:
        raise AssertionError(
            "Embedding dimension must be positive."
        )

    print()
    print("=" * 70)
    print("EMBEDDING SANITY VALIDATION")
    print("=" * 70)

    print(
        f"Chunks embedded: {len(embedded_chunks)}"
    )
    print(
        f"Embedding dimension: {dimension}"
    )
    print("Embedding dimensions consistent: PASS")


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("EMBEDDING QUALITY CHECKS & SANITY TESTS")
    print("=" * 70)

    print()
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Embedding base URL: {EMBEDDING_BASE_URL}")

    print()
    print("=" * 70)
    print("BUILDING CHUNK EMBEDDINGS")
    print("=" * 70)

    embedded_chunks = embed_chunks(CHUNK_RECORDS)

    validate_embeddings(embedded_chunks)

    results = []

    for case in TEST_CASES:

        result = run_test_case(
            case,
            embedded_chunks,
        )

        results.append(result)

        print_test_result(result)

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    failed = len(results) - passed

    surprising = identify_surprising_cases(results)

    print()
    print("=" * 70)
    print("SANITY REPORT")
    print("=" * 70)

    print(f"Tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    print()
    print("Test outcomes:")

    for result in results:
        print(
            f"  - {result['name']}: "
            f"{'PASS' if result['passed'] else 'FAIL'}"
        )
        print(
            f"    expected: "
            f"{result['expected_source']}"
        )
        print(
            f"    top: "
            f"{result['top_source']}"
        )
        print(
            f"    top score: "
            f"{result['top_score']:.6f}"
        )
        print(
            f"    expected position: "
            f"{result['expected_position']}"
        )

    print()
    print("=" * 70)
    print("SURPRISING / RISK CASE")
    print("=" * 70)

    for case in surprising:
        print(
            f"Type: {case['type']}"
        )
        print(
            f"Case: {case['name']}"
        )
        print(
            f"Explanation: {case['explanation']}"
        )
        print()

    print("=" * 70)
    print("PIPELINE CHECKS")
    print("=" * 70)

    print("Same embedding model for query and chunks: PASS")
    print("Embedding dimensions consistent: PASS")
    print("Cosine similarity used consistently: PASS")
    print("Known relevance cases executed: PASS")
    print("Ranking inspected for every test: PASS")

    print()
    print("=" * 70)
    print("QUALITY SANITY TESTS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()