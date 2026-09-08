from pathlib import Path

from .document_loader import load_corpus
from .document_chunker import paragraph_chunks
from .text_cleaner import clean


def get_document_type(source: str) -> str:
    """
    Return the document format based on its filename.
    """
    suffix = Path(source).suffix.lower()

    if suffix == ".pdf":
        return "pdf"

    if suffix == ".txt":
        return "txt"

    if suffix == ".md":
        return "markdown"

    if suffix in {".html", ".htm"}:
        return "html"

    return "unknown"


def find_char_position(text: str, chunk: str, start_search: int = 0) -> int:
    """
    Find the character position of a chunk in the cleaned document.

    Returns -1 if the chunk cannot be located.
    """
    return text.find(chunk, start_search)


def tag_chunks(
    source: str,
    text: str,
    chunks: list[str],
) -> list[dict]:
    """
    Attach consistent metadata to every chunk.

    Every chunk has:
    - text
    - metadata.source
    - metadata.chunk_index
    - metadata.char_start
    - metadata.char_end
    - metadata.section
    - metadata.document_type
    """
    tagged_chunks = []
    search_position = 0
    document_type = get_document_type(source)

    for index, chunk in enumerate(chunks):
        char_start = find_char_position(
            text,
            chunk,
            search_position,
        )

        if char_start == -1:
            char_start = search_position

        char_end = char_start + len(chunk)

        tagged_chunks.append(
            {
                "text": chunk,
                "metadata": {
                    "source": source,
                    "chunk_index": index,
                    "char_start": char_start,
                    "char_end": char_end,
                    "section": "unknown",
                    "document_type": document_type,
                },
            }
        )

        search_position = char_end

    return tagged_chunks


def trace_chunk(chunk: dict) -> None:
    """
    Demonstrate how a retrieved chunk can be traced back
    to its source using metadata.
    """
    metadata = chunk["metadata"]

    print("\n" + "=" * 70)
    print("CHUNK TRACE")
    print("=" * 70)

    print(f"Source: {metadata['source']}")
    print(f"Document type: {metadata['document_type']}")
    print(f"Chunk index: {metadata['chunk_index']}")
    print(f"Character range: {metadata['char_start']} - {metadata['char_end']}")
    print(f"Section: {metadata['section']}")

    print("\nRetrieved text:")
    print(chunk["text"])

    print("\nTrace result:")
    print(
        f"This chunk came from "
        f"{metadata['source']} "
        f"(chunk {metadata['chunk_index']}, "
        f"characters {metadata['char_start']}-{metadata['char_end']})."
    )


def main() -> None:
    """
    Load, clean, chunk, tag, and trace a sample document.
    """
    documents = load_corpus("sample_corpus")

    if not documents:
        print("No documents were loaded.")
        return

    # Use the same document selected in the chunking assignment.
    document = documents[0]

    source = document["source"]
    cleaned_text = clean(document["text"])

    # Use paragraph chunking because it was selected in 3.21.
    chunks = paragraph_chunks(cleaned_text)

    tagged_chunks = tag_chunks(
        source=source,
        text=cleaned_text,
        chunks=chunks,
    )

    print("=" * 70)
    print("CHUNK METADATA & SOURCE TRACKING")
    print("=" * 70)

    print(f"\nSource document: {source}")
    print(f"Document type: {get_document_type(source)}")
    print(f"Total chunks: {len(tagged_chunks)}")

    # ---------------------------------------------------------
    # Show sample chunks with metadata.
    # ---------------------------------------------------------
    for chunk in tagged_chunks[:3]:
        print("\n" + "-" * 70)
        print("CHUNK")
        print("-" * 70)

        print("Text:")
        print(chunk["text"])

        print("\nMetadata:")
        for key, value in chunk["metadata"].items():
            print(f"  {key}: {value}")

    # ---------------------------------------------------------
    # Verify metadata structure consistency.
    # ---------------------------------------------------------
    required_fields = {
        "source",
        "chunk_index",
        "char_start",
        "char_end",
        "section",
        "document_type",
    }

    structure_is_consistent = all(
        set(chunk["metadata"].keys()) == required_fields
        for chunk in tagged_chunks
    )

    print("\n" + "=" * 70)
    print("METADATA VERIFICATION")
    print("=" * 70)

    print(
        f"Every chunk contains source: "
        f"{all('source' in chunk['metadata'] for chunk in tagged_chunks)}"
    )

    print(
        f"Every chunk contains position metadata: "
        f"{all('char_start' in chunk['metadata'] for chunk in tagged_chunks)}"
    )

    print(
        f"Metadata structure consistent: "
        f"{structure_is_consistent}"
    )

    # ---------------------------------------------------------
    # Demonstrate retrieval tracing.
    # In a real RAG system this chunk would come from the
    # vector database after retrieval.
    # ---------------------------------------------------------
    if tagged_chunks:
        trace_chunk(tagged_chunks[0])


if __name__ == "__main__":
    main()