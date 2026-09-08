from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}


def load_text(path: Path) -> str:
    """Load a supported document and return its contents as plain text."""
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(path)
        return "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    if suffix in {".txt", ".md"}:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    if suffix in {".html", ".htm"}:
        html = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
        return BeautifulSoup(html, "html.parser").get_text(
            " ",
            strip=True,
        )

    raise ValueError(f"unsupported format: {suffix}")


def load_corpus(corpus_dir: str | Path) -> list[dict[str, str]]:
    """Load all supported documents while surviving individual failures."""
    corpus_path = Path(corpus_dir)
    documents = []

    if not corpus_path.exists():
        print(f"SKIP corpus directory: {corpus_path} does not exist")
        return documents

    for path in sorted(corpus_path.rglob("*")):
        if not path.is_file():
            continue

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"SKIP {path.name}: unsupported format")
            continue

        try:
            text = load_text(path)

            documents.append(
                {
                    "source": path.name,
                    "text": text,
                }
            )

            sample = " ".join(text.split())[:100]

            print(
                f"OK   {path.name}: "
                f"{len(text)} chars | "
                f"sample={sample!r}"
            )

        except Exception as error:
            print(f"SKIP {path.name}: {error}")

    return documents


def main() -> None:
    corpus = load_corpus("sample_corpus")

    print("\n" + "=" * 70)
    print("DOCUMENT INTAKE SUMMARY")
    print("=" * 70)
    print(f"Loaded documents: {len(corpus)}")

    for document in corpus:
        print(
            f"- {document['source']}: "
            f"{len(document['text'])} chars"
        )


if __name__ == "__main__":
    main()