from pathlib import Path
import json
import uuid

import requests

from .config import QDRANT_URL, QDRANT_API_KEY


# ============================================================
# CONFIGURATION
# ============================================================

COLLECTION_NAME = "traderule_rag_chunks"

EMBEDDING_STORE = Path(
    "backend/src/embedding_store.json"
)

BATCH_SIZE = 2

# Test point created during Assignment 3.30.
# It is removed before indexing the real corpus.
TEST_POINT_ID = 1001

# Namespace used to generate deterministic UUIDs for
# application-level stable chunk IDs.
#
# Example:
# customs-0 -> same UUID every time
# export-0  -> same UUID every time
CHUNK_ID_NAMESPACE = uuid.UUID(
    "7b8f4d2a-8f3e-4a9a-9f2c-5d1c7e9b2a11"
)


# ============================================================
# QDRANT HTTP HELPERS
# ============================================================

def headers():
    """
    Build HTTP headers for Qdrant REST requests.

    Local Qdrant does not require an API key.
    Production Qdrant deployments may use one.
    """

    result = {
        "Content-Type": "application/json",
    }

    if QDRANT_API_KEY:
        result["api-key"] = QDRANT_API_KEY

    return result


def qdrant_request(method, path, **kwargs):
    """
    Send an HTTP request to Qdrant.

    The Qdrant response body is included in errors to make
    debugging much easier.
    """

    url = (
        f"{QDRANT_URL.rstrip('/')}/"
        f"{path.lstrip('/')}"
    )

    response = requests.request(
        method,
        url,
        headers=headers(),
        timeout=30,
        **kwargs,
    )

    if not response.ok:
        raise RuntimeError(
            f"Qdrant request failed: "
            f"{response.status_code} "
            f"{response.reason}\n"
            f"URL: {url}\n"
            f"Response: {response.text}"
        )

    return response.json()


# ============================================================
# LOAD EMBEDDINGS
# ============================================================

def load_embeddings():
    """
    Load embeddings generated during Assignment 3.28.

    The actual embedding_store.json format is:

    {
        "customs-0": {
            "id": "customs-0",
            "text": "...",
            "metadata": {...},
            "embedding": [...]
        },
        "export-0": {
            ...
        }
    }

    The dictionary values are converted into a list of
    embedding records.
    """

    if not EMBEDDING_STORE.exists():
        raise FileNotFoundError(
            f"Embedding store not found: "
            f"{EMBEDDING_STORE}"
        )

    with EMBEDDING_STORE.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    # --------------------------------------------------------
    # Format 1: list
    # --------------------------------------------------------

    if isinstance(data, list):
        return data

    # --------------------------------------------------------
    # Format 2: dictionary
    # --------------------------------------------------------

    if isinstance(data, dict):

        # Example:
        #
        # {
        #     "records": [...]
        # }

        if "records" in data:
            return data["records"]

        # Example:
        #
        # {
        #     "embeddings": [...]
        # }

        if "embeddings" in data:
            return data["embeddings"]

        # Actual Assignment 3.28 format:
        #
        # {
        #     "customs-0": {...},
        #     "export-0": {...},
        #     "import-0": {...}
        # }

        if data and all(
            isinstance(value, dict)
            for value in data.values()
        ):
            return list(data.values())

    raise ValueError(
        "Unsupported embedding store format. "
        "Expected a list, a dictionary containing "
        "records, or a dictionary keyed by stable "
        "chunk ID."
    )


# ============================================================
# QDRANT ID GENERATION
# ============================================================

def qdrant_id(chunk_id):
    """
    Convert an application-level stable chunk ID into
    a deterministic UUID.

    Qdrant accepts UUIDs as point IDs.

    The UUID is deterministic, meaning:

        customs-0 -> same UUID every run

    This makes re-indexing safe because the same chunk
    always maps to the same Qdrant point.
    """

    return str(
        uuid.uuid5(
            CHUNK_ID_NAMESPACE,
            str(chunk_id),
        )
    )


# ============================================================
# RECORD PREPARATION
# ============================================================

def to_vector_record(chunk):
    """
    Convert an embedding-store record into a Qdrant-ready
    record.

    The original stable chunk ID is preserved as chunk_id.
    """

    metadata = chunk.get(
        "metadata",
        {},
    )

    original_id = chunk["id"]

    return {
        # Qdrant-compatible UUID
        "id": qdrant_id(original_id),

        # Original application-level stable ID
        "chunk_id": original_id,

        # Embedding vector
        "vector": chunk["embedding"],

        # Original source text
        "text": chunk["text"],

        # Retrieval/filtering metadata
        "metadata": {
            "source": metadata.get(
                "source"
            ),
            "chunk_index": metadata.get(
                "chunk_index"
            ),
            "section": metadata.get(
                "section"
            ),
            "document_type": metadata.get(
                "document_type"
            ),
        },
    }


def validate_prepared_record(record):
    """
    Validate a record before inserting it into Qdrant.
    """

    required_fields = [
        "id",
        "chunk_id",
        "vector",
        "text",
        "metadata",
    ]

    for field in required_fields:

        if field not in record:
            return (
                False,
                f"Missing field: {field}",
            )

    if not record["id"]:
        return (
            False,
            "Empty Qdrant ID",
        )

    if not record["chunk_id"]:
        return (
            False,
            "Empty stable chunk ID",
        )

    if not record["vector"]:
        return (
            False,
            "Empty embedding vector",
        )

    if not record["text"]:
        return (
            False,
            "Empty source text",
        )

    if not isinstance(
        record["metadata"],
        dict,
    ):
        return (
            False,
            "Metadata is not a dictionary",
        )

    return True, None


# ============================================================
# BATCHING
# ============================================================

def batches(items, size):
    """
    Yield records in fixed-size batches.
    """

    for start in range(
        0,
        len(items),
        size,
    ):
        yield items[
            start:start + size
        ]


# ============================================================
# COLLECTION COUNT
# ============================================================

def collection_count():
    """
    Return the exact number of points in Qdrant.
    """

    result = qdrant_request(
        "POST",
        (
            f"/collections/"
            f"{COLLECTION_NAME}/"
            f"points/count"
        ),
        json={
            "exact": True,
        },
    )

    return result["result"]["count"]


# ============================================================
# DELETE 3.30 TEST RECORD
# ============================================================

def delete_test_record():
    """
    Remove the numeric test point created during Assignment 3.30.

    This ensures the final collection contains only the actual
    corpus embeddings.
    """

    try:

        result = qdrant_request(
            "POST",
            (
                f"/collections/"
                f"{COLLECTION_NAME}/"
                f"points/delete?wait=true"
            ),
            json={
                "points": [
                    TEST_POINT_ID
                ],
            },
        )

        return True, result

    except RuntimeError as error:

        # If the test point is already absent, continue.
        if "404" in str(error):
            return True, None

        raise


# ============================================================
# INSERT BATCH
# ============================================================

def insert_batch(batch):
    """
    Insert a batch of records into Qdrant.
    """

    points = []

    for record in batch:

        points.append(
            {
                "id": record["id"],

                "vector": record["vector"],

                "payload": {
                    # Stable application-level ID
                    "chunk_id": record["chunk_id"],

                    # Original source text
                    "text": record["text"],

                    # Source and retrieval metadata
                    "metadata": record["metadata"],
                },
            }
        )

    return qdrant_request(
        "PUT",
        (
            f"/collections/"
            f"{COLLECTION_NAME}/"
            f"points?wait=true"
        ),
        json={
            "points": points,
        },
    )


# ============================================================
# READBACK
# ============================================================

def read_back(qdrant_point_id):
    """
    Read one point back from Qdrant.
    """

    result = qdrant_request(
        "POST",
        (
            f"/collections/"
            f"{COLLECTION_NAME}/"
            f"points"
        ),
        json={
            "ids": [
                qdrant_point_id
            ],
            "with_vector": True,
            "with_payload": True,
        },
    )

    points = result["result"]

    if not points:
        raise ValueError(
            f"Record not found: "
            f"{qdrant_point_id}"
        )

    return points[0]


# ============================================================
# SPOT-CHECK VALIDATION
# ============================================================

def validate_spot_check(
    original,
    stored,
):
    """
    Compare the original prepared record against
    the Qdrant record read back from the database.
    """

    original_metadata = (
        original["metadata"]
    )

    stored_payload = (
        stored["payload"]
    )

    stored_metadata = (
        stored_payload["metadata"]
    )

    # --------------------------------------------------------
    # QDRANT ID
    # --------------------------------------------------------

    qdrant_id_match = (
        str(stored["id"])
        == str(original["id"])
    )

    # --------------------------------------------------------
    # STABLE APPLICATION ID
    # --------------------------------------------------------

    chunk_id_match = (
        stored_payload["chunk_id"]
        == original["chunk_id"]
    )

    # --------------------------------------------------------
    # SOURCE TEXT
    # --------------------------------------------------------

    text_match = (
        stored_payload["text"]
        == original["text"]
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata_match = (
        stored_metadata["source"]
        == original_metadata.get(
            "source"
        )
        and
        stored_metadata["chunk_index"]
        == original_metadata.get(
            "chunk_index"
        )
        and
        stored_metadata["section"]
        == original_metadata.get(
            "section"
        )
        and
        stored_metadata["document_type"]
        == original_metadata.get(
            "document_type"
        )
    )

    # --------------------------------------------------------
    # VECTOR LENGTH
    #
    # IMPORTANT:
    # The prepared record uses "vector", not "embedding".
    # --------------------------------------------------------

    vector_length_match = (
        len(stored["vector"])
        == len(original["vector"])
    )

    return {
        "qdrant_id": qdrant_id_match,
        "chunk_id": chunk_id_match,
        "text": text_match,
        "metadata": metadata_match,
        "vector_length": vector_length_match,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("EMBEDDING INDEXING & METADATA STORAGE")
    print("=" * 70)

    print()
    print(
        f"Qdrant URL: {QDRANT_URL}"
    )

    print(
        f"Collection: {COLLECTION_NAME}"
    )

    print(
        f"Embedding store: "
        f"{EMBEDDING_STORE}"
    )

    print(
        f"Batch size: {BATCH_SIZE}"
    )

    # ========================================================
    # LOAD EMBEDDINGS
    # ========================================================

    print()
    print("=" * 70)
    print("LOAD EMBEDDINGS")
    print("=" * 70)

    embedded_chunks = (
        load_embeddings()
    )

    print(
        f"Corpus embeddings loaded: "
        f"{len(embedded_chunks)}"
    )

    # ========================================================
    # PREPARE RECORDS
    # ========================================================

    records = []

    preparation_failures = []

    for chunk in embedded_chunks:

        try:

            record = to_vector_record(
                chunk
            )

            valid, error = (
                validate_prepared_record(
                    record
                )
            )

            if not valid:

                preparation_failures.append(
                    {
                        "id": chunk.get(
                            "id"
                        ),
                        "error": error,
                    }
                )

                continue

            records.append(record)

        except Exception as error:

            preparation_failures.append(
                {
                    "id": chunk.get(
                        "id"
                    ),
                    "error": str(error),
                }
            )

    print(
        f"Records prepared for indexing: "
        f"{len(records)}"
    )

    if preparation_failures:

        print()
        print(
            "Record preparation failures:"
        )

        for failure in (
            preparation_failures
        ):

            print(
                f"- {failure['id']}: "
                f"{failure['error']}"
            )

        raise RuntimeError(
            "Record preparation failed."
        )

    print(
        "Record preparation validation: PASS"
    )

    # ========================================================
    # SHOW STABLE ID MAPPING
    # ========================================================

    print()
    print(
        "Stable ID → Qdrant UUID mapping:"
    )

    for record in records:

        print(
            f"{record['chunk_id']} "
            f"→ {record['id']}"
        )

    # ========================================================
    # CLEANUP OLD TEST RECORD
    # ========================================================

    print()
    print("=" * 70)
    print("CLEANUP PREVIOUS TEST RECORD")
    print("=" * 70)

    removed, _ = (
        delete_test_record()
    )

    if removed:

        print(
            f"Assignment 3.30 test point "
            f"{TEST_POINT_ID}: removed/absent"
        )

        print(
            "Test record cleanup: PASS"
        )

    # ========================================================
    # BULK INDEXING
    # ========================================================

    print()
    print("=" * 70)
    print("BULK INDEXING")
    print("=" * 70)

    inserted = 0

    failures = []

    total_batches = 0

    for batch_number, batch in enumerate(
        batches(
            records,
            BATCH_SIZE,
        ),
        start=1,
    ):

        total_batches += 1

        batch_ids = [
            record["chunk_id"]
            for record in batch
        ]

        print()

        print(
            f"Batch {batch_number}: "
            f"{len(batch)} records"
        )

        print(
            f"Stable IDs: {batch_ids}"
        )

        try:

            insert_batch(batch)

            inserted += len(batch)

            print(
                "Batch insertion: PASS"
            )

        except Exception as error:

            failures.append(
                {
                    "batch_start_id": (
                        batch[0]["chunk_id"]
                    ),
                    "error": str(error),
                }
            )

            print(
                "Batch insertion: FAIL"
            )

            print(
                f"Error: {error}"
            )

    # ========================================================
    # INDEX COUNT VALIDATION
    # ========================================================

    print()
    print("=" * 70)
    print("INDEX COUNT VALIDATION")
    print("=" * 70)

    indexed_count = (
        collection_count()
    )

    expected_count = len(records)

    print(
        f"Expected records: "
        f"{expected_count}"
    )

    print(
        f"Inserted this run: "
        f"{inserted}"
    )

    print(
        f"Indexed count in Qdrant: "
        f"{indexed_count}"
    )

    print(
        f"Failures: "
        f"{failures if failures else 'None'}"
    )

    count_match = (
        indexed_count
        == expected_count
    )

    print(
        "Indexed count matches "
        "expected count: "
        f"{'PASS' if count_match else 'FAIL'}"
    )

    # ========================================================
    # SPOT-CHECK READBACK
    # ========================================================

    print()
    print("=" * 70)
    print("SPOT-CHECK READBACK")
    print("=" * 70)

    if not records:

        raise RuntimeError(
            "No records available for spot-check."
        )

    sample = records[0]

    print(
        f"Original stable ID: "
        f"{sample['chunk_id']}"
    )

    print(
        f"Qdrant point ID: "
        f"{sample['id']}"
    )

    stored = read_back(
        sample["id"]
    )

    validation = (
        validate_spot_check(
            sample,
            stored,
        )
    )

    # --------------------------------------------------------
    # QDRANT ID
    # --------------------------------------------------------

    print(
        f"Readback Qdrant ID: "
        f"{stored['id']}"
    )

    print(
        "Qdrant ID validation: "
        f"{'PASS' if validation['qdrant_id'] else 'FAIL'}"
    )

    # --------------------------------------------------------
    # STABLE ID
    # --------------------------------------------------------

    print(
        f"Readback stable ID: "
        f"{stored['payload']['chunk_id']}"
    )

    print(
        "Stable chunk ID validation: "
        f"{'PASS' if validation['chunk_id'] else 'FAIL'}"
    )

    # --------------------------------------------------------
    # SOURCE TEXT
    # --------------------------------------------------------

    print(
        "Source text validation: "
        f"{'PASS' if validation['text'] else 'FAIL'}"
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    print(
        "Metadata validation: "
        f"{'PASS' if validation['metadata'] else 'FAIL'}"
    )

    # --------------------------------------------------------
    # VECTOR
    # --------------------------------------------------------

    print(
        f"Vector length: "
        f"{len(stored['vector'])}"
    )

    print(
        "Vector length validation: "
        f"{'PASS' if validation['vector_length'] else 'FAIL'}"
    )

    # --------------------------------------------------------
    # READBACK DETAILS
    # --------------------------------------------------------

    print()

    print(
        "Source:",
        stored["payload"][
            "metadata"
        ]["source"],
    )

    print(
        "Chunk index:",
        stored["payload"][
            "metadata"
        ]["chunk_index"],
    )

    print(
        "Section:",
        stored["payload"][
            "metadata"
        ]["section"],
    )

    print(
        "Document type:",
        stored["payload"][
            "metadata"
        ]["document_type"],
    )

    print(
        "Text preview:",
        stored["payload"][
            "text"
        ][:120],
    )

    all_spot_check_passed = all(
        validation.values()
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print()
    print("=" * 70)
    print("INDEXING VALIDATION")
    print("=" * 70)

    all_embeddings_loaded = (
        len(records)
        == len(embedded_chunks)
    )

    vectors_text_metadata_stored = all(
        bool(record["vector"])
        and bool(record["text"])
        and isinstance(
            record["metadata"],
            dict,
        )
        for record in records
    )

    no_failures = not failures

    print(
        "All corpus embeddings loaded: "
        f"{'PASS' if all_embeddings_loaded else 'FAIL'}"
    )

    print(
        "Vector + text + metadata stored: "
        f"{'PASS' if vectors_text_metadata_stored else 'FAIL'}"
    )

    print(
        "Indexed count matches chunk count: "
        f"{'PASS' if count_match else 'FAIL'}"
    )

    print(
        "Spot-check integrity: "
        f"{'PASS' if all_spot_check_passed else 'FAIL'}"
    )

    print(
        "Failures: "
        f"{'None' if no_failures else failures}"
    )

    # ========================================================
    # FINAL RESULT
    # ========================================================

    final_pass = (
        all_embeddings_loaded
        and vectors_text_metadata_stored
        and no_failures
        and count_match
        and all_spot_check_passed
    )

    print()
    print("=" * 70)

    print(
        "EMBEDDING INDEXING: "
        f"{'PASS' if final_pass else 'FAIL'}"
    )

    print("=" * 70)

    if not final_pass:

        raise RuntimeError(
            "Embedding indexing validation failed."
        )


if __name__ == "__main__":
    main()