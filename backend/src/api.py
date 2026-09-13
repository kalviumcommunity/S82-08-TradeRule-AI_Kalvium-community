"""
3.44 Backend API for the RAG Service

TradeRule AI FastAPI service.

Provides:
    POST /query

The endpoint:
    1. Validates the incoming question.
    2. Calls the existing hallucination-guarded RAG pipeline.
    3. Returns a structured JSON response.
    4. Exposes grounded answers with source metadata.
    5. Handles validation and server errors.
    6. Uses environment-based configuration through the
       existing RAG modules.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# =====================================================================
# PATH + ENVIRONMENT CONFIGURATION
# =====================================================================

# Allow imports from backend/src when running:
#     uvicorn api:app --reload
#
# This is intentionally kept local to the API entry point.
SRC_DIR = os.path.dirname(os.path.abspath(__file__))

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

load_dotenv()


# =====================================================================
# EXISTING TRADE RULE AI PIPELINE
# =====================================================================

from hallucination_guardrails import (
    REFUSAL_MESSAGE,
    TOP_K,
    create_embedding_client,
    create_generation_client,
    guarded_answer,
)


# =====================================================================
# API CONFIGURATION
# =====================================================================

API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

API_TITLE = "TradeRule AI RAG API"
API_VERSION = "1.0.0"


# =====================================================================
# CLIENT STATE
# =====================================================================

embedding_client: Any = None
generation_client: Any = None


# =====================================================================
# REQUEST / RESPONSE MODELS
# =====================================================================


class QueryRequest(BaseModel):
    """
    Request body accepted by POST /query.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Compliance question to answer using TradeRule AI.",
    )


class Source(BaseModel):
    """
    Source information returned with the grounded answer.
    """

    citation: str
    source: str | None = None
    chunk_id: str | None = None
    chunk_index: Any = None


class QueryResponse(BaseModel):
    """
    Structured response returned by POST /query.
    """

    answer: str
    sources: list[Source]
    status: str

    retrieval_count: int
    top_score: float
    supporting_chunks: int
    threshold: float
    reason: str


class HealthResponse(BaseModel):
    """
    Response returned by GET /health.
    """

    status: str
    service: str
    version: str


# =====================================================================
# CLIENT INITIALIZATION
# =====================================================================


def initialize_clients() -> None:
    """
    Create the embedding and generation clients once when
    the API starts.

    API keys and model configuration are loaded by the
    existing RAG modules from environment variables.
    """

    global embedding_client
    global generation_client

    embedding_client = create_embedding_client()
    generation_client = create_generation_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI application lifecycle.

    Clients are initialized when the server starts.
    """

    initialize_clients()

    yield


# =====================================================================
# FASTAPI APPLICATION
# =====================================================================


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Backend API for the TradeRule AI grounded "
        "RAG compliance assistant."
    ),
    lifespan=lifespan,
)


# =====================================================================
# HEALTH ENDPOINT
# =====================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Check whether the API service is running.
    """

    return HealthResponse(
        status="ok",
        service=API_TITLE,
        version=API_VERSION,
    )


# =====================================================================
# QUERY ENDPOINT
# =====================================================================


@app.post(
    "/query",
    response_model=QueryResponse,
)
def query_rag(request: QueryRequest) -> QueryResponse:
    """
    Run a user question through the existing guarded RAG pipeline.

    Flow:

        Request
          ↓
        Pydantic validation
          ↓
        guarded_answer()
          ↓
        Embedding
          ↓
        Qdrant retrieval
          ↓
        Hallucination guardrail
          ↓
        Grounded Gemini answer
          ↓
        Citation validation
          ↓
        Structured JSON response
    """

    if embedding_client is None or generation_client is None:
        raise HTTPException(
            status_code=503,
            detail="RAG service clients are not initialized.",
        )

    try:
        question = request.question.strip()

        # Defensive validation after Pydantic validation.
        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question cannot be empty.",
            )

        result = guarded_answer(
            question=question,
            embedding_client=embedding_client,
            generation_client=generation_client,
            k=TOP_K,
        )

        sources = [
            Source(
                citation=str(source.get("citation", "")),
                source=(
                    str(source["source"])
                    if source.get("source") is not None
                    else None
                ),
                chunk_id=(
                    str(source["chunk_id"])
                    if source.get("chunk_id") is not None
                    else None
                ),
                chunk_index=source.get("chunk_index"),
            )
            for source in result.sources
        ]

        return QueryResponse(
            answer=result.answer,
            sources=sources,
            status=result.status,
            retrieval_count=result.retrieval_count,
            top_score=result.top_score,
            supporting_chunks=result.supporting_chunks,
            threshold=result.threshold,
            reason=result.reason,
        )

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print(f"RAG API error: {error}")

        raise HTTPException(
            status_code=500,
            detail="RAG service failed.",
        )


# =====================================================================
# APPLICATION ENTRY POINT
# =====================================================================


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
    )