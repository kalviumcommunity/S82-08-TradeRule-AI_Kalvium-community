import re
import unicodedata

from .document_loader import load_corpus


def clean(text: str) -> str:
    """
    Clean extracted document text for downstream RAG processing.

    Cleaning steps:
    1. Normalize Unicode using NFKC.
    2. Repair common UTF-8/Windows-1252 mojibake artifacts.
    3. Normalize line endings.
    4. Remove page-number boilerplate.
    5. Remove repeated document headers and footers.
    6. Collapse repeated spaces and tabs.
    7. Remove unnecessary spaces at line boundaries.
    8. Collapse excessive blank lines.
    """

    # ---------------------------------------------------------
    # 1. Normalize Unicode
    # ---------------------------------------------------------
    text = unicodedata.normalize("NFKC", text)

    # ---------------------------------------------------------
    # 2. Repair common encoding / mojibake artifacts
    # ---------------------------------------------------------
    replacements = {
        "â€™": "'",
        "â€œ": '"',
        "â€\x9d": '"',
        "â€“": "–",
        "â€”": "—",
        "Â ": " ",
    }

    for broken, fixed in replacements.items():
        text = text.replace(broken, fixed)

    # ---------------------------------------------------------
    # 3. Normalize line endings
    # ---------------------------------------------------------
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # ---------------------------------------------------------
    # 4. Remove page-number boilerplate
    #
    # Handles:
    #   Page 1 of 3
    #   Page 2 of 12
    #   PAGE 3 OF 10
    #
    # This works whether the page marker is on its own
    # line or appears inline after HTML extraction.
    # ---------------------------------------------------------
    text = re.sub(
        r"(?i)\bPage\s+\d+\s+of\s+\d+\b",
        "",
        text,
    )

    # ---------------------------------------------------------
    # 5. Remove repeated document headers / footers
    #
    # Handles both standalone and inline occurrences.
    # ---------------------------------------------------------
    boilerplate_patterns = [
        r"(?i)\bTradeRule AI Compliance Document\b",
        r"(?i)\bConfidential\b",
        r"(?i)\bwww\.traderule-ai\.example\b",
    ]

    for pattern in boilerplate_patterns:
        text = re.sub(pattern, "", text)

    # ---------------------------------------------------------
    # 6. Collapse repeated spaces and tabs
    # ---------------------------------------------------------
    text = re.sub(r"[ \t]+", " ", text)

    # ---------------------------------------------------------
    # 7. Remove spaces at the beginning/end of lines
    # ---------------------------------------------------------
    text = re.sub(r"(?m)^[ \t]+", "", text)
    text = re.sub(r"(?m)[ \t]+$", "", text)

    # ---------------------------------------------------------
    # 8. Collapse excessive blank lines
    # ---------------------------------------------------------
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_corpus(documents: list[dict[str, str]]) -> list[dict[str, str]]:
    """
    Apply the same cleaning function to every document.

    Source identity is preserved while only the text content
    is transformed.
    """
    cleaned_documents = []

    for document in documents:
        cleaned_documents.append(
            {
                "source": document["source"],
                "text": clean(document["text"]),
            }
        )

    return cleaned_documents


def main() -> None:
    """
    Load the sample corpus and demonstrate the cleaning pipeline.
    """
    documents = load_corpus("sample_corpus")

    print("=" * 70)
    print("TEXT EXTRACTION & CLEANING PIPELINE")
    print("=" * 70)

    cleaned_documents = []

    for document in documents:
        before = document["text"]
        after = clean(before)

        cleaned_documents.append(
            {
                "source": document["source"],
                "text": after,
            }
        )

        print(f"\nSOURCE: {document['source']}")
        print(f"LENGTH: {len(before)} -> {len(after)} chars")

        print("\nBEFORE:")
        print(before[:180].replace("\n", "\\n"))

        print("\nAFTER:")
        print(after[:180].replace("\n", "\\n"))

    print("\n" + "=" * 70)
    print("CLEANING SUMMARY")
    print("=" * 70)
    print(f"Documents processed: {len(cleaned_documents)}")
    print("Cleaning function applied consistently: YES")


if __name__ == "__main__":
    main()