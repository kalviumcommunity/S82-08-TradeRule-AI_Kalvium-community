import requests

from .config import (
    QDRANT_URL,
    QDRANT_API_KEY,
)


# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_NAME = "traderule_rag_chunks"

# gemini-embedding-001 produces 3072-dimensional embeddings
# in our existing embedding pipeline.
VECTOR_DIMENSION = 3072

DISTANCE_METRIC = "Cosine"

TEST_POINT_ID = 1001

TEST_TEXT = (
    "International shipment compliance requires exporters "
    "to verify product classification and destination requirements."
)

TEST_METADATA = {
    "source": "customs_requirements.txt",
    "chunk_index": 0,
    "section": "export compliance",
    "document_type": "txt",
}


# ============================================================
# HTTP HELPERS
# ============================================================

def headers():
    result = {
        "Content-Type": "application/json",
    }

    if QDRANT_API_KEY:
        result["api-key"] = QDRANT_API_KEY

    return result


def qdrant_request(
    method,
    path,
    **kwargs,
):
    """
    Send an HTTP request to Qdrant.
    """

    if not QDRANT_URL:
        raise ValueError(
            "QDRANT_URL is not configured."
        )

    url = f"{QDRANT_URL.rstrip('/')}/{path.lstrip('/')}"

    response = requests.request(
        method=method,
        url=url,
        headers=headers(),
        timeout=30,
        **kwargs,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CONNECTION TEST
# ============================================================

def test_connection():

    result = qdrant_request(
        "GET",
        "/collections",
    )

    collections = result.get(
        "result",
        {},
    ).get(
        "collections",
        [],
    )

    print()
    print("=" * 70)
    print("QDRANT CONNECTION")
    print("=" * 70)

    print(
        f"Qdrant URL: {QDRANT_URL}"
    )

    print(
        "Reachable: PASS"
    )

    print(
        f"Existing collections: "
        f"{len(collections)}"
    )


# ============================================================
# COLLECTION SETUP
# ============================================================

def collection_exists():

    result = qdrant_request(
        "GET",
        f"/collections/{COLLECTION_NAME}",
    )

    return result.get("status") == "ok"


def create_collection():

    try:
        exists = collection_exists()

    except requests.HTTPError as error:

        response = error.response

        if response is not None and response.status_code == 404:
            exists = False
        else:
            raise

    if exists:

        print()
        print(
            f"Collection already exists: "
            f"{COLLECTION_NAME}"
        )

        return

    payload = {
        "vectors": {
            "size": VECTOR_DIMENSION,
            "distance": DISTANCE_METRIC,
        }
    }

    qdrant_request(
        "PUT",
        f"/collections/{COLLECTION_NAME}",
        json=payload,
    )

    print()
    print(
        f"Collection created: "
        f"{COLLECTION_NAME}"
    )


# ============================================================
# COLLECTION VALIDATION
# ============================================================

def validate_collection():

    result = qdrant_request(
        "GET",
        f"/collections/{COLLECTION_NAME}",
    )

    collection_info = result["result"]

    vectors_config = (
        collection_info["config"]["params"]["vectors"]
    )

    actual_dimension = vectors_config["size"]
    actual_distance = vectors_config["distance"]

    print()
    print("=" * 70)
    print("COLLECTION VALIDATION")
    print("=" * 70)

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Expected vector dimension: "
        f"{VECTOR_DIMENSION}"
    )

    print(
        f"Actual vector dimension: "
        f"{actual_dimension}"
    )

    if actual_dimension != VECTOR_DIMENSION:
        raise AssertionError(
            "Collection dimension does not match "
            "embedding dimension."
        )

    print(
        "Vector dimension: PASS"
    )

    print(
        f"Expected distance: "
        f"{DISTANCE_METRIC}"
    )

    print(
        f"Actual distance: "
        f"{actual_distance}"
    )

    if actual_distance.lower() != DISTANCE_METRIC.lower():
        raise AssertionError(
            "Collection distance metric is incorrect."
        )

    print(
        "Cosine distance configuration: PASS"
    )


# ============================================================
# TEST VECTOR
# ============================================================

def build_test_vector():

    vector = [0.0] * VECTOR_DIMENSION

    # Non-zero deterministic test vector.
    vector[0] = 1.0

    return vector


# ============================================================
# INSERT TEST RECORD
# ============================================================

def insert_test_record():

    vector = build_test_vector()

    payload = {
        "text": TEST_TEXT,
        "metadata": TEST_METADATA,
    }

    request_body = {
        "points": [
            {
                "id": TEST_POINT_ID,
                "vector": vector,
                "payload": payload,
            }
        ]
    }

    qdrant_request(
        "PUT",
        f"/collections/{COLLECTION_NAME}/points",
        params={
            "wait": "true",
        },
        json=request_body,
    )

    print()
    print("=" * 70)
    print("TEST RECORD INSERT")
    print("=" * 70)

    print(
        f"Inserted point ID: "
        f"{TEST_POINT_ID}"
    )

    print(
        f"Vector length: "
        f"{len(vector)}"
    )

    print(
        "Vector + text + metadata: PASS"
    )


# ============================================================
# READBACK
# ============================================================

def read_back_test_record():

    request_body = {
        "ids": [
            TEST_POINT_ID,
        ],
        "with_vector": True,
        "with_payload": True,
    }

    result = qdrant_request(
        "POST",
        f"/collections/{COLLECTION_NAME}/points",
        json=request_body,
    )

    records = result.get(
        "result",
        [],
    )

    if not records:
        raise AssertionError(
            "Test record could not be read back."
        )

    return records[0]


# ============================================================
# READBACK VALIDATION
# ============================================================

def validate_readback(record):

    record_id = record["id"]
    vector = record["vector"]
    payload = record["payload"]

    text = payload.get("text")
    metadata = payload.get("metadata")

    print()
    print("=" * 70)
    print("READBACK VALIDATION")
    print("=" * 70)

    print(
        f"Readback ID: {record_id}"
    )

    if record_id != TEST_POINT_ID:
        raise AssertionError(
            "Readback ID does not match inserted ID."
        )

    print(
        "ID validation: PASS"
    )

    print(
        f"Vector length: {len(vector)}"
    )

    if len(vector) != VECTOR_DIMENSION:
        raise AssertionError(
            "Readback vector dimension is incorrect."
        )

    print(
        "Vector dimension validation: PASS"
    )

    print()
    print(
        f"Text: {text}"
    )

    if text != TEST_TEXT:
        raise AssertionError(
            "Readback text does not match inserted text."
        )

    print(
        "Source text validation: PASS"
    )

    print()
    print(
        f"Metadata: {metadata}"
    )

    required_fields = {
        "source",
        "chunk_index",
        "section",
        "document_type",
    }

    missing = required_fields - set(metadata.keys())

    if missing:
        raise AssertionError(
            f"Missing metadata fields: {missing}"
        )

    if metadata != TEST_METADATA:
        raise AssertionError(
            "Readback metadata does not match "
            "inserted metadata."
        )

    print(
        "Metadata validation: PASS"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("VECTOR DATABASE SETUP & COLLECTION DESIGN")
    print("=" * 70)

    print()
    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Vector dimension: "
        f"{VECTOR_DIMENSION}"
    )

    print(
        f"Distance metric: "
        f"{DISTANCE_METRIC}"
    )

    test_connection()

    create_collection()

    validate_collection()

    insert_test_record()

    record = read_back_test_record()

    validate_readback(record)

    print()
    print("=" * 70)
    print("VECTOR DATABASE VALIDATION")
    print("=" * 70)

    print(
        "Qdrant connection: PASS"
    )

    print(
        "Collection creation/configuration: PASS"
    )

    print(
        "Correct vector dimension: PASS"
    )

    print(
        "Vector + text + metadata schema: PASS"
    )

    print(
        "Test record insertion: PASS"
    )

    print(
        "Test record readback: PASS"
    )

    print()
    print("=" * 70)
    print("VECTOR DATABASE SETUP: PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()