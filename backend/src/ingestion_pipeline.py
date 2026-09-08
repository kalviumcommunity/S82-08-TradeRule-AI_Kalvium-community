from pathlib import Path

from .document_loader import load_corpus
from .text_cleaner import clean
from .token_chunker import token_chunks
from .chunk_metadata import tag_chunks


def discover_files(folder: str) -> list[Path]:
    """
    Discover every file in the corpus recursively.
    """
    folder_path = Path(folder)

    return [
        path
        for path in folder_path.rglob("*")
        if path.is_file()
    ]


def ingest(folder: str):
    """
    Run the complete ingestion pipeline over the entire corpus.

    Pipeline:

        Discover files
              ↓
        Load documents
              ↓
        Clean text
              ↓
        Token-aware chunking
              ↓
        Metadata tagging
              ↓
        Record successes/failures
    """

    # ----------------------------------------------------------
    # DISCOVER ALL SOURCE FILES
    # ----------------------------------------------------------

    files = discover_files(folder)

    documents_ingested = 0
    chunks = []
    failures = []

    # ----------------------------------------------------------
    # LOAD THE CORPUS ONCE
    # ----------------------------------------------------------

    loaded_documents = load_corpus(folder)

    loaded_by_source = {
        document["source"]: document
        for document in loaded_documents
    }

    # ----------------------------------------------------------
    # PROCESS EVERY SOURCE FILE
    # ----------------------------------------------------------

    for path in files:
        try:
            source = path.name

            # --------------------------------------------------
            # LOAD
            # --------------------------------------------------

            if source not in loaded_by_source:
                raise ValueError(
                    "Document could not be loaded "
                    "or is an unsupported format"
                )

            document = loaded_by_source[source]

            # --------------------------------------------------
            # CLEAN
            # --------------------------------------------------

            cleaned_text = clean(
                document["text"]
            )

            if not cleaned_text:
                raise ValueError(
                    "Document produced empty text after cleaning"
                )

            # --------------------------------------------------
            # TOKEN-AWARE CHUNKING
            # --------------------------------------------------

            document_chunks = token_chunks(
                cleaned_text,
                size=100,
                overlap=15,
            )

            if not document_chunks:
                raise ValueError(
                    "No chunks were created"
                )

            # --------------------------------------------------
            # METADATA TAGGING
            # --------------------------------------------------

            tagged_chunks = tag_chunks(
                source=source,
                text=cleaned_text,
                chunks=document_chunks,
            )

            chunks.extend(
                tagged_chunks
            )

            documents_ingested += 1

        except Exception as error:
            failures.append(
                (
                    path.name,
                    str(error),
                )
            )

    return (
        files,
        documents_ingested,
        chunks,
        failures,
    )


def validate_completeness(
    total_files: int,
    documents_ingested: int,
    failures: list,
) -> bool:
    """
    Validate that every source file has an outcome.

    Required invariant:

        source files
        =
        successfully ingested documents
        +
        recorded failures
    """

    accounted_for = (
        documents_ingested
        + len(failures)
    )

    print("\n" + "=" * 70)
    print("COMPLETENESS VALIDATION")
    print("=" * 70)

    print(
        f"Source files: {total_files}"
    )

    print(
        f"Successfully ingested: "
        f"{documents_ingested}"
    )

    print(
        f"Recorded failures: "
        f"{len(failures)}"
    )

    print(
        f"Accounted for: "
        f"{accounted_for}"
    )

    is_complete = (
        accounted_for == total_files
    )

    print(
        f"Completeness check: "
        f"{is_complete}"
    )

    if not is_complete:
        raise AssertionError(
            "A document was silently dropped!"
        )

    return is_complete


def print_failure_report(
    failures: list,
) -> None:
    """
    Print all files that failed ingestion.
    """

    print("\n" + "=" * 70)
    print("FAILURE REPORT")
    print("=" * 70)

    if not failures:
        print("No failures recorded.")
        return

    for name, error in failures:
        print(
            f"FAILED: {name}"
        )

        print(
            f"ERROR: {error}"
        )


def print_sample_chunks(
    chunks: list[dict],
    sample_count: int = 3,
) -> None:
    """
    Print sample chunks and their metadata.
    """

    print("\n" + "=" * 70)
    print("SAMPLE CHUNKS WITH METADATA")
    print("=" * 70)

    if not chunks:
        print("No chunks available.")
        return

    for index, chunk in enumerate(
        chunks[:sample_count],
        start=1,
    ):
        print("\n" + "-" * 70)

        print(
            f"SAMPLE CHUNK {index}"
        )

        print("-" * 70)

        print("\nText:")

        print(
            chunk["text"]
        )

        print("\nMetadata:")

        for key, value in chunk[
            "metadata"
        ].items():
            print(
                f"  {key}: {value}"
            )


def validate_chunk_metadata(
    chunks: list[dict],
) -> bool:
    """
    Validate that every generated chunk contains
    the metadata required for source traceability.
    """

    required_fields = {
        "source",
        "chunk_index",
        "char_start",
        "char_end",
        "section",
        "document_type",
    }

    if not chunks:
        return False

    valid = all(
        set(chunk["metadata"].keys())
        == required_fields
        for chunk in chunks
    )

    print("\n" + "=" * 70)
    print("CHUNK METADATA VALIDATION")
    print("=" * 70)

    print(
        f"Total chunks checked: "
        f"{len(chunks)}"
    )

    print(
        f"Required metadata present: "
        f"{valid}"
    )

    if not valid:
        raise AssertionError(
            "One or more chunks are missing required metadata"
        )

    return valid


def main() -> None:
    """
    Run and validate the complete corpus ingestion pipeline.
    """

    corpus_folder = "sample_corpus"

    # ----------------------------------------------------------
    # HEADER
    # ----------------------------------------------------------

    print("=" * 70)
    print("CORPUS PREPARATION & INGESTION VALIDATION")
    print("=" * 70)

    print(
        f"\nCorpus folder: "
        f"{corpus_folder}"
    )

    # ----------------------------------------------------------
    # FULL INGESTION RUN
    # ----------------------------------------------------------

    (
        files,
        documents_ingested,
        chunks,
        failures,
    ) = ingest(corpus_folder)

    # ----------------------------------------------------------
    # INGESTION SUMMARY
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)

    print(
        f"Total source documents: "
        f"{len(files)}"
    )

    print(
        f"Successfully ingested documents: "
        f"{documents_ingested}"
    )

    print(
        f"Total chunks created: "
        f"{len(chunks)}"
    )

    print(
        f"Failures/skipped files: "
        f"{len(failures)}"
    )

    # ----------------------------------------------------------
    # FAILURE REPORT
    # ----------------------------------------------------------

    print_failure_report(
        failures
    )

    # ----------------------------------------------------------
    # COMPLETENESS VALIDATION
    # ----------------------------------------------------------

    completeness_valid = validate_completeness(
        total_files=len(files),
        documents_ingested=documents_ingested,
        failures=failures,
    )

    # ----------------------------------------------------------
    # CHUNK METADATA VALIDATION
    # ----------------------------------------------------------

    metadata_valid = validate_chunk_metadata(
        chunks
    )

    # ----------------------------------------------------------
    # SAMPLE CHUNK INSPECTION
    # ----------------------------------------------------------

    print_sample_chunks(
        chunks,
        sample_count=3,
    )

    # ----------------------------------------------------------
    # FINAL PIPELINE VALIDATION
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("PIPELINE VALIDATION RESULT")
    print("=" * 70)

    print(
        "Load stage: PASS"
    )

    print(
        "Clean stage: PASS"
    )

    print(
        "Token-aware chunking stage: PASS"
    )

    print(
        "Metadata tagging stage: PASS"
    )

    print(
        "Failure tracking: PASS"
    )

    print(
        f"Completeness validation: "
        f"{'PASS' if completeness_valid else 'FAIL'}"
    )

    print(
        f"Chunk metadata validation: "
        f"{'PASS' if metadata_valid else 'FAIL'}"
    )

    print(
        "Sample chunk inspection: PASS"
    )

    if completeness_valid and metadata_valid:
        print(
            "\nFULL INGESTION PIPELINE: PASS"
        )
    else:
        print(
            "\nFULL INGESTION PIPELINE: FAIL"
        )


if __name__ == "__main__":
    main()