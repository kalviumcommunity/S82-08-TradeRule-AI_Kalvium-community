"""
3.47 Streaming Responses & Citation Display

TradeRule AI streaming RAG pipeline.

Features:
- Retrieves relevant chunks from Qdrant
- Applies retrieval guardrails
- Sends citation metadata before answer tokens
- Streams Gemini response progressively
- Validates citations after generation
- Handles streaming failures gracefully
"""

from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator

from google import genai
from google.genai import types

from context_augmentation import (
    embed_query,
    retrieve_chunks,
)

from hallucination_guardrails import (
    MIN_TOP_SCORE,
    MIN_SUPPORTING_CHUNKS,
    REFUSAL_MESSAGE,
)

from citation_attribution import (
    build_cited_prompt,
    validate_citations,
)


# ============================================================
# CONFIGURATION
# ============================================================

TOP_K = int(
    os.getenv(
        "TOP_K",
        "5",
    )
)

CHAT_MODEL = os.getenv(
    "CHAT_MODEL",
    "gemini-2.5-flash",
)


# ============================================================
# GENERIC CHUNK HELPERS
# ============================================================

def get_payload(
    chunk: Any,
) -> dict[str, Any]:
    """
    Safely extract Qdrant payload data.
    """

    if not isinstance(chunk, dict):
        return {}

    payload = chunk.get(
        "payload"
    )

    if isinstance(payload, dict):
        return payload

    return {}


def get_metadata(
    chunk: Any,
) -> dict[str, Any]:
    """
    Safely extract metadata from a chunk.
    """

    if not isinstance(chunk, dict):
        return {}

    metadata = chunk.get(
        "metadata"
    )

    if isinstance(metadata, dict):
        return metadata

    payload = get_payload(chunk)

    payload_metadata = payload.get(
        "metadata"
    )

    if isinstance(
        payload_metadata,
        dict,
    ):
        return payload_metadata

    return payload


def get_chunk_text(
    chunk: Any,
) -> str:
    """
    Extract source text from a retrieved chunk.
    """

    if not isinstance(chunk, dict):
        return ""

    if chunk.get("text"):
        return str(
            chunk["text"]
        )

    payload = get_payload(chunk)

    if payload.get("text"):
        return str(
            payload["text"]
        )

    metadata = get_metadata(chunk)

    if metadata.get("text"):
        return str(
            metadata["text"]
        )

    return ""


def get_chunk_source(
    chunk: Any,
) -> str:
    """
    Extract source/document name.
    """

    if not isinstance(chunk, dict):
        return "Unknown source"

    for key in (
        "source",
        "document",
        "filename",
        "file_name",
    ):
        if chunk.get(key) is not None:
            return str(
                chunk[key]
            )

    payload = get_payload(chunk)

    for key in (
        "source",
        "document",
        "filename",
        "file_name",
    ):
        if payload.get(key) is not None:
            return str(
                payload[key]
            )

    metadata = get_metadata(chunk)

    for key in (
        "source",
        "document",
        "filename",
        "file_name",
    ):
        if metadata.get(key) is not None:
            return str(
                metadata[key]
            )

    return "Unknown source"


def get_chunk_id_value(
    chunk: Any,
) -> str:
    """
    Extract stable chunk ID.
    """

    if not isinstance(chunk, dict):
        return "Unknown chunk"

    for key in (
        "chunk_id",
        "id",
    ):
        if chunk.get(key) is not None:
            return str(
                chunk[key]
            )

    payload = get_payload(chunk)

    for key in (
        "chunk_id",
        "id",
    ):
        if payload.get(key) is not None:
            return str(
                payload[key]
            )

    metadata = get_metadata(chunk)

    for key in (
        "chunk_id",
        "id",
    ):
        if metadata.get(key) is not None:
            return str(
                metadata[key]
            )

    return "Unknown chunk"


def get_chunk_section(
    chunk: Any,
) -> str | None:
    """
    Extract optional section metadata.
    """

    metadata = get_metadata(chunk)

    value = metadata.get(
        "section"
    )

    if value is not None:
        return str(value)

    return None


def get_chunk_index(
    chunk: Any,
) -> Any:
    """
    Extract chunk index metadata.
    """

    metadata = get_metadata(chunk)

    return metadata.get(
        "chunk_index"
    )


def get_score(
    chunk: Any,
) -> float:
    """
    Extract similarity score.
    """

    if not isinstance(chunk, dict):
        return 0.0

    value = chunk.get(
        "score",
        0.0,
    )

    try:
        return float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0


# ============================================================
# RETRIEVAL GUARDRAIL
# ============================================================

def evaluate_stream_retrieval(
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Evaluate whether retrieved context is strong enough
    to allow answer generation.
    """

    if not chunks:
        return {
            "accepted": False,
            "retrieval_count": 0,
            "top_score": 0.0,
            "supporting_chunks": 0,
        }

    scores = [
        get_score(chunk)
        for chunk in chunks
    ]

    top_score = max(
        scores,
        default=0.0,
    )

    supporting_chunks = sum(
        1
        for score in scores
        if score >= MIN_TOP_SCORE
    )

    accepted = (
        top_score >= MIN_TOP_SCORE
        and
        supporting_chunks
        >= MIN_SUPPORTING_CHUNKS
    )

    return {
        "accepted": accepted,
        "retrieval_count": len(
            chunks
        ),
        "top_score": top_score,
        "supporting_chunks": (
            supporting_chunks
        ),
    }


# ============================================================
# CITATION SOURCES
# ============================================================

def build_stream_sources(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Convert retrieved chunks into frontend-friendly
    citation objects.
    """

    sources = []

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        sources.append(
            {
                "id": f"source-{index}",
                "label": f"[{index}]",
                "document": get_chunk_source(
                    chunk
                ),
                "chunk_id": get_chunk_id_value(
                    chunk
                ),
                "chunk_index": get_chunk_index(
                    chunk
                ),
                "section": get_chunk_section(
                    chunk
                ),
                "text": get_chunk_text(
                    chunk
                ),
            }
        )

    return sources


# ============================================================
# SSE
# ============================================================

def make_sse_event(
    payload: dict[str, Any],
) -> str:
    """
    Convert a Python dictionary to an SSE event.
    """

    return (
        "data: "
        + json.dumps(
            payload,
            ensure_ascii=False,
        )
        + "\n\n"
    )


# ============================================================
# STREAMING RAG
# ============================================================

async def stream_rag_response(
    question: str,
    embedding_client: Any,
    generation_client: genai.Client,
) -> AsyncGenerator[str, None]:
    """
    Complete streaming RAG pipeline.

    Event types:

        citations
        token
        done
        error
    """

    try:
        # ----------------------------------------------------
        # EMBEDDING
        # ----------------------------------------------------

        query_vector = embed_query(
            embedding_client,
            question,
        )

        # ----------------------------------------------------
        # RETRIEVAL
        # ----------------------------------------------------

        chunks = retrieve_chunks(
            query_vector,
            k=TOP_K,
        )

        # ----------------------------------------------------
        # RETRIEVAL GUARDRAIL
        # ----------------------------------------------------

        evaluation = (
            evaluate_stream_retrieval(
                chunks
            )
        )

        if not evaluation["accepted"]:
            yield make_sse_event(
                {
                    "type": "error",
                    "message": (
                        "I don't have enough "
                        "reliable context to "
                        "answer that."
                    ),
                    "retrieval_count": evaluation[
                        "retrieval_count"
                    ],
                    "top_score": evaluation[
                        "top_score"
                    ],
                    "supporting_chunks": evaluation[
                        "supporting_chunks"
                    ],
                }
            )

            return

        # ----------------------------------------------------
        # BUILD CITATIONS
        # ----------------------------------------------------

        sources = build_stream_sources(
            chunks
        )

        # ----------------------------------------------------
        # SEND CITATIONS BEFORE TOKENS
        # ----------------------------------------------------

        yield make_sse_event(
            {
                "type": "citations",
                "sources": sources,
                "retrieval_count": evaluation[
                    "retrieval_count"
                ],
                "top_score": evaluation[
                    "top_score"
                ],
                "supporting_chunks": evaluation[
                    "supporting_chunks"
                ],
                "threshold": MIN_TOP_SCORE,
            }
        )

        # ----------------------------------------------------
        # BUILD GROUNDED PROMPT
        # ----------------------------------------------------

        prompt, citation_map = (
            build_cited_prompt(
                question,
                chunks,
            )
        )

        # ----------------------------------------------------
        # STREAM GEMINI RESPONSE
        # ----------------------------------------------------

        full_answer = ""

        stream = (
            generation_client.models.generate_content_stream(
                model=CHAT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1000,
                ),
            )
        )

        for response_chunk in stream:

            text = getattr(
                response_chunk,
                "text",
                None,
            )

            if not text:
                continue

            full_answer += text

            yield make_sse_event(
                {
                    "type": "token",
                    "text": text,
                }
            )

        # ----------------------------------------------------
        # VALIDATE CITATIONS
        # ----------------------------------------------------

        citation_validation = (
            validate_citations(
                full_answer,
                citation_map,
            )
        )

        if not citation_validation[
            "all_citations_valid"
        ]:
            yield make_sse_event(
                {
                    "type": "error",
                    "message": (
                        "The generated answer "
                        "could not be verified "
                        "against the retrieved "
                        "sources."
                    ),
                    "citation_validation": (
                        citation_validation
                    ),
                }
            )

            return

        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        yield make_sse_event(
            {
                "type": "done",
                "status": "answered",
                "citation_validation": (
                    citation_validation
                ),
            }
        )

    except Exception as error:

        print(
            "Streaming RAG error:",
            error,
        )

        yield make_sse_event(
            {
                "type": "error",
                "message": (
                    "The answer stopped "
                    "streaming. Please retry."
                ),
            }
        )