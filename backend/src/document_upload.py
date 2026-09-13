from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

from fastapi import HTTPException, UploadFile


# ============================================================
# MODULE PATH
# ============================================================

SRC_DIR = Path(__file__).resolve().parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ============================================================
# EXISTING PIPELINE
# ============================================================

from document_loader import load_text
from text_cleaner import clean
from token_chunker import token_chunks
from chunk_metadata import tag_chunks
from batch_embedding import (
    embed_with_retry,
    validate_embedding_response,
)
from index_embeddings import (
    to_vector_record,
    insert_batch,
)


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = SRC_DIR.parent.parent

UPLOAD_DIR = Path(
    os.getenv(
        "UPLOAD_DIR",
        str(PROJECT_ROOT / "uploads"),
    )
)

MAX_UPLOAD_SIZE_MB = int(
    os.getenv("MAX_UPLOAD_SIZE_MB", "10")
)

MAX_UPLOAD_SIZE_BYTES = (
    MAX_UPLOAD_SIZE_MB * 1024 * 1024
)

CHUNK_SIZE = int(
    os.getenv("UPLOAD_CHUNK_SIZE", "100")
)

CHUNK_OVERLAP = int(
    os.getenv("UPLOAD_CHUNK_OVERLAP", "15")
)

EMBEDDING_BATCH_SIZE = int(
    os.getenv("EMBEDDING_BATCH_SIZE", "2")
)

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf",
}


# ============================================================
# SAFE FILENAME
# ============================================================

def safe_filename(filename: str | None) -> str:

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    name = Path(filename).name

    name = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        name,
    )

    if not name or name in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    return name


# ============================================================
# VALIDATE UPLOAD
# ============================================================

def validate_upload(file: UploadFile) -> str:

    filename = safe_filename(file.filename)

    suffix = Path(filename).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=(
                "Unsupported file type. "
                "Supported formats: .txt, .md, .pdf"
            ),
        )

    return suffix


# ============================================================
# STORE UPLOAD
# ============================================================

async def store_upload(file: UploadFile) -> Path:

    validate_upload(file)

    filename = safe_filename(file.filename)

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File exceeds the maximum allowed "
                f"size of {MAX_UPLOAD_SIZE_MB} MB."
            ),
        )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = UPLOAD_DIR / filename

    path.write_bytes(content)

    return path


# ============================================================
# EMBEDDING
# ============================================================

def embed_chunks(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    if not chunks:
        raise ValueError(
            "No chunks were generated from the document."
        )

    embedded_chunks = []

    for start in range(
        0,
        len(chunks),
        EMBEDDING_BATCH_SIZE,
    ):

        batch = chunks[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        texts = [
            chunk["text"]
            for chunk in batch
        ]

        response = embed_with_retry(texts)

        validate_embedding_response(
            response,
            expected_count=len(batch),
        )

        for chunk, embedding_item in zip(
            batch,
            response.data,
        ):

            metadata = chunk["metadata"]

            source = metadata["source"]

            chunk_index = metadata["chunk_index"]

            chunk_id = (
                f"{source}-{chunk_index}"
            )

            embedded_chunks.append(
                {
                    "id": chunk_id,
                    "text": chunk["text"],
                    "metadata": metadata,
                    "embedding": embedding_item.embedding,
                }
            )

    return embedded_chunks


# ============================================================
# QDRANT INDEXING
# ============================================================

def index_embedded_chunks(
    embedded_chunks: list[dict[str, Any]],
) -> int:

    if not embedded_chunks:
        raise ValueError(
            "No embedded chunks available for indexing."
        )

    records = [
        to_vector_record(chunk)
        for chunk in embedded_chunks
    ]

    indexed = 0

    for start in range(
        0,
        len(records),
        EMBEDDING_BATCH_SIZE,
    ):

        batch = records[
            start:start + EMBEDDING_BATCH_SIZE
        ]

        insert_batch(batch)

        indexed += len(batch)

    return indexed


# ============================================================
# COMPLETE PROCESSING PIPELINE
# ============================================================

def process_uploaded_document(
    path: Path,
) -> dict[str, Any]:

    # 1. Load
    raw_text = load_text(path)

    if not raw_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document contains no readable text.",
        )

    # 2. Clean
    cleaned_text = clean(raw_text)

    if not cleaned_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Document contains no usable text after cleaning.",
        )

    # 3. Chunk
    chunks = token_chunks(
        cleaned_text,
        size=CHUNK_SIZE,
        overlap=CHUNK_OVERLAP,
    )

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Document produced no chunks.",
        )

    # 4. Metadata
    tagged_chunks = tag_chunks(
        source=path.name,
        text=cleaned_text,
        chunks=chunks,
    )

    # 5. Embeddings
    embedded_chunks = embed_chunks(
        tagged_chunks
    )

    # 6. Qdrant
    indexed = index_embedded_chunks(
        embedded_chunks
    )

    return {
        "document": str(path),
        "chunks": len(tagged_chunks),
        "embedded": len(embedded_chunks),
        "indexed": indexed,
    }