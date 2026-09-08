from .document_loader import load_corpus
from .text_cleaner import clean

import tiktoken


# Tokenizer used for token-aware chunk sizing.
# This provides consistent token counting for the assignment.
ENCODER = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """
    Return the number of tokens in the given text.
    """
    return len(ENCODER.encode(text))


def token_chunks(
    text: str,
    size: int = 100,
    overlap: int = 15,
) -> list[str]:
    """
    Split text into token-sized chunks with controlled overlap.

    Example:
        size=100, overlap=15

    means each chunk contains at most 100 tokens and the next
    chunk begins with the final 15 tokens of the previous chunk.
    """
    if size <= 0:
        raise ValueError("chunk size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= size:
        raise ValueError("overlap must be smaller than chunk size")

    tokens = ENCODER.encode(text)

    chunks = []

    start = 0
    step = size - overlap

    while start < len(tokens):
        chunk_tokens = tokens[start:start + size]

        if not chunk_tokens:
            break

        chunk = ENCODER.decode(chunk_tokens)

        chunks.append(chunk)

        start += step

    return chunks


def token_chunks_without_overlap(
    text: str,
    size: int = 100,
) -> list[str]:
    """
    Create token-based chunks without overlap.

    This is used as the baseline for comparing the effect
    of overlap.
    """
    return token_chunks(
        text,
        size=size,
        overlap=0,
    )


def chunk_stats(chunks: list[str]) -> dict[str, float]:
    """
    Calculate basic statistics for a list of chunks.
    """
    if not chunks:
        return {
            "count": 0,
            "average_tokens": 0.0,
        }

    token_sizes = [
        count_tokens(chunk)
        for chunk in chunks
    ]

    return {
        "count": len(chunks),
        "average_tokens": (
            sum(token_sizes) / len(token_sizes)
        ),
    }


def print_chunks(
    name: str,
    chunks: list[str],
) -> None:
    """
    Print chunk statistics and the first three chunks.
    """
    stats = chunk_stats(chunks)

    print(f"\n{name}")
    print("-" * 70)

    print(
        f"Chunk count: {stats['count']}"
    )

    print(
        f"Average chunk size: "
        f"{stats['average_tokens']:.2f} tokens"
    )

    for index, chunk in enumerate(
        chunks[:3],
        start=1,
    ):
        print(
            f"\nChunk {index} "
            f"({count_tokens(chunk)} tokens):"
        )

        print(repr(chunk))


def demonstrate_boundary_context(
    text: str,
    size: int = 30,
    overlap: int = 8,
) -> None:
    """
    Demonstrate how overlap preserves boundary context.

    Two chunking configurations are compared:

    1. No overlap
    2. Controlled token overlap

    The function also verifies that the final N tokens of the
    first overlapping chunk exactly match the first N tokens
    of the next chunk.
    """
    print("\n" + "=" * 70)
    print("BOUNDARY CONTEXT DEMONSTRATION")
    print("=" * 70)

    without_overlap = token_chunks_without_overlap(
        text,
        size=size,
    )

    with_overlap = token_chunks(
        text,
        size=size,
        overlap=overlap,
    )

    # ----------------------------------------------------------
    # WITHOUT OVERLAP
    # ----------------------------------------------------------

    print("\nWITHOUT OVERLAP")
    print("-" * 70)

    for index, chunk in enumerate(
        without_overlap[:2],
        start=1,
    ):
        print(
            f"Chunk {index} "
            f"({count_tokens(chunk)} tokens):"
        )

        print(chunk)

    # ----------------------------------------------------------
    # WITH OVERLAP
    # ----------------------------------------------------------

    print("\nWITH OVERLAP")
    print("-" * 70)

    for index, chunk in enumerate(
        with_overlap[:2],
        start=1,
    ):
        print(
            f"Chunk {index} "
            f"({count_tokens(chunk)} tokens):"
        )

        print(chunk)

    # ----------------------------------------------------------
    # EXACT OVERLAP VERIFICATION
    # ----------------------------------------------------------

    if len(with_overlap) >= 2:
        first_tokens = ENCODER.encode(
            with_overlap[0]
        )

        second_tokens = ENCODER.encode(
            with_overlap[1]
        )

        expected_overlap = first_tokens[-overlap:]
        actual_overlap = second_tokens[:overlap]

        exact_overlap = (
            expected_overlap == actual_overlap
        )

        print("\nOVERLAP CHECK")
        print("-" * 70)

        print(
            f"Configured overlap: "
            f"{overlap} tokens"
        )

        print(
            f"Exact positional overlap preserved: "
            f"{exact_overlap}"
        )

        print(
            f"Verified overlapping tokens: "
            f"{len(actual_overlap)}"
        )

        print(
            "\nOverlapping boundary text:"
        )

        print(
            ENCODER.decode(actual_overlap)
        )

    else:
        print("\nOVERLAP CHECK")
        print("-" * 70)

        print(
            "Only one chunk was generated, "
            "so no adjacent chunk boundary exists "
            "to verify overlap."
        )


def main() -> None:
    """
    Run the complete token-aware chunking demonstration.
    """

    # ----------------------------------------------------------
    # LOAD DOCUMENTS
    # ----------------------------------------------------------

    documents = load_corpus(
        "sample_corpus"
    )

    if not documents:
        print("No documents were loaded.")
        return

    # Use the first document for the main demonstration.
    document = documents[0]

    source = document["source"]

    raw_text = document["text"]

    # ----------------------------------------------------------
    # CLEAN DOCUMENT
    # ----------------------------------------------------------

    cleaned_text = clean(
        raw_text
    )

    # ----------------------------------------------------------
    # MAIN HEADER
    # ----------------------------------------------------------

    print("=" * 70)
    print("TOKEN-AWARE CHUNKING")
    print("=" * 70)

    print(
        f"\nSource document: {source}"
    )

    print(
        f"Cleaned text length: "
        f"{len(cleaned_text)} characters"
    )

    print(
        f"Total document tokens: "
        f"{count_tokens(cleaned_text)}"
    )

    # ----------------------------------------------------------
    # CHUNK CONFIGURATION
    # ----------------------------------------------------------

    chunk_size = 100

    overlap = 15

    print("\nConfiguration:")

    print(
        f"Chunk size: "
        f"{chunk_size} tokens"
    )

    print(
        f"Overlap: "
        f"{overlap} tokens"
    )

    print(
        f"Overlap percentage: "
        f"{(overlap / chunk_size) * 100:.1f}%"
    )

    # ----------------------------------------------------------
    # TOKEN-AWARE CHUNKING
    # ----------------------------------------------------------

    chunks = token_chunks(
        cleaned_text,
        size=chunk_size,
        overlap=overlap,
    )

    print_chunks(
        "TOKEN-AWARE CHUNKS",
        chunks,
    )

    # ----------------------------------------------------------
    # NO-OVERLAP BASELINE
    # ----------------------------------------------------------

    no_overlap = token_chunks_without_overlap(
        cleaned_text,
        size=chunk_size,
    )

    # ----------------------------------------------------------
    # OVERLAP COST COMPARISON
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("OVERLAP COST COMPARISON")
    print("=" * 70)

    print(
        f"No overlap: "
        f"{len(no_overlap)} chunks"
    )

    print(
        f"15-token overlap: "
        f"{len(chunks)} chunks"
    )

    print(
        "\nThe overlapping configuration may create "
        "additional embedding work because boundary "
        "tokens are intentionally repeated."
    )

    print(
        "For larger documents, overlap can increase "
        "the total number of tokens processed and "
        "therefore increase embedding and storage cost."
    )

    # ----------------------------------------------------------
    # BOUNDARY DEMONSTRATION
    # ----------------------------------------------------------

    demonstrate_boundary_context(
        cleaned_text,
        size=30,
        overlap=8,
    )

    # ----------------------------------------------------------
    # JUSTIFICATION
    # ----------------------------------------------------------

    print("\n" + "=" * 70)
    print("CHUNK SIZE & OVERLAP JUSTIFICATION")
    print("=" * 70)

    print(
        "\nChosen configuration: "
        "100-token chunks with 15-token overlap."
    )

    print(
        "\nWhy token-aware sizing:"
    )

    print(
        "Token-based sizing provides a consistent way "
        "to control how much text is placed into each "
        "chunk. This is important for RAG systems because "
        "model context windows and input processing are "
        "token-oriented."
    )

    print(
        "\nWhy 100 tokens:"
    )

    print(
        "The 100-token size is appropriate for the small "
        "sample corpus used in this assignment and "
        "demonstrates explicit token-based sizing. "
        "Production values should be tuned using retrieval "
        "quality experiments and the target model's "
        "context-window requirements."
    )

    print(
        "\nWhy 15-token overlap:"
    )

    print(
        "The 15-token overlap provides approximately "
        "15% repeated boundary context. This helps preserve "
        "information when an important compliance statement "
        "crosses a chunk boundary."
    )

    print(
        "\nCost tradeoff:"
    )

    print(
        "Overlap duplicates tokens across adjacent chunks. "
        "This can increase embedding work, vector storage, "
        "and the amount of retrieved context passed to the "
        "language model. Therefore, overlap should be large "
        "enough to preserve boundary context but small enough "
        "to avoid unnecessary duplication."
    )

    print(
        "\nTop-k and context-window interaction:"
    )

    print(
        "If more chunks are retrieved with a larger top-k "
        "value, more chunk tokens may be passed into the "
        "model context. Larger chunks or excessive overlap "
        "can therefore consume the context budget faster. "
        "Chunk size, overlap, and top-k should be selected "
        "together."
    )

    print(
        "\nProduction consideration:"
    )

    print(
        "The current implementation uses the tiktoken "
        "cl100k_base tokenizer for this assignment. "
        "The final production configuration should use "
        "token accounting appropriate to the selected "
        "embedding and model stack and should be validated "
        "experimentally."
    )


if __name__ == "__main__":
    main()