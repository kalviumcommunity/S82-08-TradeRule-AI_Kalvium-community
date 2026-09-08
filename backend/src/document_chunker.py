from .document_loader import load_corpus
from .text_cleaner import clean


def fixed_chunks(
    text: str,
    size: int = 120,
    overlap: int = 20,
) -> list[str]:
    """
    Split text into fixed-size chunks with overlap.

    The overlap helps preserve context when an important
    sentence crosses a chunk boundary.
    """
    if size <= 0:
        raise ValueError("chunk size must be greater than zero")

    if overlap < 0:
        raise ValueError("overlap cannot be negative")

    if overlap >= size:
        raise ValueError("overlap must be smaller than chunk size")

    chunks = []
    start = 0
    step = size - overlap

    while start < len(text):
        chunk = text[start:start + size].strip()

        if chunk:
            chunks.append(chunk)

        start += step

    return chunks


def paragraph_chunks(text: str) -> list[str]:
    """
    Split text using paragraph boundaries.

    Empty paragraphs are ignored.
    """
    return [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]


def chunk_stats(chunks: list[str]) -> dict[str, float]:
    """Return chunk count and average chunk size."""
    if not chunks:
        return {
            "count": 0,
            "average_size": 0,
        }

    sizes = [len(chunk) for chunk in chunks]

    return {
        "count": len(chunks),
        "average_size": sum(sizes) / len(sizes),
    }


def print_strategy(
    name: str,
    chunks: list[str],
) -> None:
    """Print statistics and sample chunks for a strategy."""
    stats = chunk_stats(chunks)

    print(f"\n{name}")
    print("-" * 70)
    print(f"Chunk count: {stats['count']}")
    print(f"Average chunk size: {stats['average_size']:.2f} characters")

    for index, chunk in enumerate(chunks[:3], start=1):
        print(f"\nChunk {index} ({len(chunk)} chars):")
        print(repr(chunk))


def main() -> None:
    """
    Load and clean the corpus, then compare two chunking
    strategies on the same document.
    """
    documents = load_corpus("sample_corpus")

    if not documents:
        print("No documents were loaded.")
        return

    # ---------------------------------------------------------
    # Choose one document for a controlled comparison.
    # Both strategies operate on exactly the same cleaned text.
    # ---------------------------------------------------------
    selected_document = documents[0]

    source = selected_document["source"]
    raw_text = selected_document["text"]
    cleaned_text = clean(raw_text)

    print("=" * 70)
    print("DOCUMENT CHUNKING STRATEGY COMPARISON")
    print("=" * 70)

    print(f"\nSource document: {source}")
    print(f"Raw text length: {len(raw_text)} chars")
    print(f"Cleaned text length: {len(cleaned_text)} chars")

    # ---------------------------------------------------------
    # Strategy 1: Fixed-size + overlap
    # ---------------------------------------------------------
    fixed = fixed_chunks(
        cleaned_text,
        size=120,
        overlap=20,
    )

    # ---------------------------------------------------------
    # Strategy 2: Paragraph-based
    # ---------------------------------------------------------
    paragraph = paragraph_chunks(cleaned_text)

    print_strategy(
        "STRATEGY 1 — FIXED-SIZE + OVERLAP",
        fixed,
    )

    print_strategy(
        "STRATEGY 2 — PARAGRAPH CHUNKING",
        paragraph,
    )

    # ---------------------------------------------------------
    # Comparison
    # ---------------------------------------------------------
    fixed_stats = chunk_stats(fixed)
    paragraph_stats = chunk_stats(paragraph)

    print("\n" + "=" * 70)
    print("STRATEGY COMPARISON")
    print("=" * 70)

    print(
        f"Fixed-size: "
        f"{fixed_stats['count']} chunks, "
        f"average {fixed_stats['average_size']:.2f} chars"
    )

    print(
        f"Paragraph: "
        f"{paragraph_stats['count']} chunks, "
        f"average {paragraph_stats['average_size']:.2f} chars"
    )

    print("\nChosen strategy: PARAGRAPH CHUNKING")

    print(
        "\nJustification: TradeRule AI contains structured compliance "
        "content such as requirements, guidelines, and policy "
        "paragraphs. Paragraph chunking preserves meaningful "
        "boundaries and reduces the chance of splitting a "
        "requirement in the middle of a sentence."
    )


if __name__ == "__main__":
    main()