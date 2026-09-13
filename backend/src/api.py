"""
3.48 Caching, Logging & Usage Monitoring
TradeRule AI RAG Backend API
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any


# ============================================================
# MODULE PATH
# ============================================================

SRC_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if SRC_DIR not in sys.path:
    sys.path.insert(
        0,
        SRC_DIR,
    )


# ============================================================
# ENVIRONMENT
# ============================================================

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# FASTAPI
# ============================================================

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    StreamingResponse,
)

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# RAG COMPONENTS
# ============================================================

from hallucination_guardrails import (
    TOP_K,
    create_embedding_client,
    create_generation_client,
    guarded_answer,
)

from document_upload import (
    store_upload,
    process_uploaded_document,
)

from streaming_rag import (
    stream_rag_response,
)


# ============================================================
# 3.48 OBSERVABILITY
# ============================================================

from rag_cache import (
    get_cached_answer,
    save_cached_answer,
)

from rag_logging import (
    log_rag_request,
)

from usage_monitoring import (
    calculate_usage,
)


# ============================================================
# API CONFIGURATION
# ============================================================

API_HOST = os.getenv(
    "API_HOST",
    "127.0.0.1",
)

API_PORT = int(
    os.getenv(
        "API_PORT",
        "8000",
    )
)

API_TITLE = os.getenv(
    "API_TITLE",
    "TradeRule AI RAG API",
)

API_VERSION = os.getenv(
    "API_VERSION",
    "1.0.0",
)


# ============================================================
# CLIENTS
# ============================================================

embedding_client: Any = None

generation_client: Any = None


# ============================================================
# REQUEST MODEL
# ============================================================

class QueryRequest(BaseModel):
    """
    Request body for RAG queries.
    """

    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description=(
            "Compliance question to answer "
            "using TradeRule AI."
        ),
    )


# ============================================================
# SOURCE MODEL
# ============================================================

class Source(BaseModel):
    """
    Retrieved source metadata.
    """

    citation: str

    source: str | None = None

    chunk_id: str | None = None

    chunk_index: Any = None


# ============================================================
# QUERY RESPONSE
# ============================================================

class QueryResponse(BaseModel):
    """
    Structured RAG response.
    """

    answer: str

    sources: list[Source]

    status: str

    retrieval_count: int

    top_score: float

    supporting_chunks: int

    threshold: float

    reason: str


# ============================================================
# DOCUMENT UPLOAD RESPONSE
# ============================================================

class DocumentUploadResponse(BaseModel):
    """
    Response returned after document indexing.
    """

    status: str

    filename: str

    summary: dict[str, Any]


# ============================================================
# HEALTH RESPONSE
# ============================================================

class HealthResponse(BaseModel):
    """
    Health check response.
    """

    status: str

    service: str

    version: str


# ============================================================
# CACHE SETTINGS
# ============================================================

def get_cache_settings() -> dict[str, Any]:
    """
    Return settings that affect a RAG response.

    These values are included in the cache key so
    responses generated under different relevant
    configurations are not mixed.
    """

    return {
        "top_k": TOP_K,
        "model": os.getenv(
            "CHAT_MODEL",
            "gemini-2.5-flash",
        ),
    }


# ============================================================
# CLIENT INITIALIZATION
# ============================================================

def initialize_clients() -> None:
    """
    Initialize embedding and generation clients.
    """

    global embedding_client
    global generation_client

    embedding_client = (
        create_embedding_client()
    )

    generation_client = (
        create_generation_client()
    )


# ============================================================
# APPLICATION LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    """
    Initialize RAG clients when the API starts.
    """

    initialize_clients()

    yield


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Backend API for the TradeRule AI "
        "grounded RAG compliance assistant."
    ),
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Check whether API is running.
    """

    return HealthResponse(
        status="ok",
        service=API_TITLE,
        version=API_VERSION,
    )


# ============================================================
# NORMAL QUERY
# ============================================================

@app.post(
    "/query",
    response_model=QueryResponse,
)
def query_rag(
    request: QueryRequest,
) -> QueryResponse:
    """
    Answer a compliance question using
    the grounded RAG pipeline.

    Includes:
        - caching
        - structured logging
        - usage tracking
        - latency measurement
    """

    if (
        embedding_client is None
        or generation_client is None
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service clients "
                "are not initialized."
            ),
        )

    question = (
        request.question.strip()
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    request_id = str(
        uuid.uuid4()
    )

    start_time = time.perf_counter()

    cache_settings = (
        get_cache_settings()
    )

    # ========================================================
    # CACHE LOOKUP
    # ========================================================

    cached_response = (
        get_cached_answer(
            question,
            cache_settings,
        )
    )

    if cached_response is not None:

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        cached_answer = (
            cached_response[
                "answer"
            ]
        )

        cached_sources = (
            cached_response[
                "sources"
            ]
        )

        log_rag_request(
            request_id=request_id,
            question=question,
            answer=cached_answer,
            sources=cached_sources,
            cache_hit=True,
            input_tokens=0,
            output_tokens=0,
            estimated_cost=0.0,
            latency_ms=latency_ms,
            status="cache_hit",
        )

        return QueryResponse(
            answer=cached_answer,
            sources=[
                Source(**source)
                for source
                in cached_sources
            ],
            status="cache_hit",
            retrieval_count=(
                cached_response[
                    "retrieval_count"
                ]
            ),
            top_score=(
                cached_response[
                    "top_score"
                ]
            ),
            supporting_chunks=(
                cached_response[
                    "supporting_chunks"
                ]
            ),
            threshold=(
                cached_response[
                    "threshold"
                ]
            ),
            reason=(
                "Response served from "
                "query cache."
            ),
        )

    # ========================================================
    # CACHE MISS → FULL RAG
    # ========================================================

    try:

        result = guarded_answer(
            question=question,
            embedding_client=(
                embedding_client
            ),
            generation_client=(
                generation_client
            ),
            k=TOP_K,
        )

        # ----------------------------------------------------
        # SOURCE SERIALIZATION
        # ----------------------------------------------------

        sources: list[
            dict[str, Any]
        ] = []

        for source in result.sources:

            sources.append(
                {
                    "citation": str(
                        source.get(
                            "citation",
                            "",
                        )
                    ),
                    "source": (
                        str(
                            source["source"]
                        )
                        if source.get(
                            "source"
                        ) is not None
                        else None
                    ),
                    "chunk_id": (
                        str(
                            source["chunk_id"]
                        )
                        if source.get(
                            "chunk_id"
                        ) is not None
                        else None
                    ),
                    "chunk_index": (
                        source.get(
                            "chunk_index"
                        )
                    ),
                }
            )

        # ----------------------------------------------------
        # LATENCY
        # ----------------------------------------------------

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        # ----------------------------------------------------
        # USAGE
        # ----------------------------------------------------

        usage = calculate_usage(
            question=question,
            prompt="",
            answer=result.answer,
            cache_hit=False,
        )

        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        log_rag_request(
            request_id=request_id,
            question=question,
            answer=result.answer,
            sources=sources,
            cache_hit=False,
            input_tokens=usage[
                "input_tokens"
            ],
            output_tokens=usage[
                "output_tokens"
            ],
            estimated_cost=usage[
                "estimated_cost"
            ],
            latency_ms=latency_ms,
            status=result.status,
        )

        # ----------------------------------------------------
        # CACHE SUCCESSFUL ANSWERS ONLY
        # ----------------------------------------------------

        if result.status == "answered":

            cached_payload = {
                "answer": result.answer,
                "sources": sources,
                "retrieval_count": (
                    result.retrieval_count
                ),
                "top_score": (
                    result.top_score
                ),
                "supporting_chunks": (
                    result.supporting_chunks
                ),
                "threshold": (
                    result.threshold
                ),
            }

            save_cached_answer(
                question,
                cached_payload,
                cache_settings,
            )

        # ----------------------------------------------------
        # RETURN
        # ----------------------------------------------------

        return QueryResponse(
            answer=result.answer,
            sources=[
                Source(**source)
                for source
                in sources
            ],
            status=result.status,
            retrieval_count=(
                result.retrieval_count
            ),
            top_score=result.top_score,
            supporting_chunks=(
                result.supporting_chunks
            ),
            threshold=result.threshold,
            reason=result.reason,
        )

    # ========================================================
    # VALIDATION ERROR
    # ========================================================

    except ValueError as error:

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        log_rag_request(
            request_id=request_id,
            question=question,
            cache_hit=False,
            latency_ms=latency_ms,
            status="validation_error",
            error=str(error),
        )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # ========================================================
    # UNEXPECTED ERROR
    # ========================================================

    except Exception as error:

        latency_ms = (
            time.perf_counter()
            - start_time
        ) * 1000

        log_rag_request(
            request_id=request_id,
            question=question,
            cache_hit=False,
            latency_ms=latency_ms,
            status="error",
            error=str(error),
        )

        print(
            f"RAG API error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="RAG service failed.",
        )


# ============================================================
# STREAMING QUERY
# ============================================================

@app.post(
    "/query/stream",
)
async def query_stream(
    request: QueryRequest,
):
    """
    Stream a grounded RAG answer using
    Server-Sent Events.
    """

    if (
        embedding_client is None
        or generation_client is None
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "RAG service clients "
                "are not initialized."
            ),
        )

    question = (
        request.question.strip()
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    return StreamingResponse(
        stream_rag_response(
            question=question,
            embedding_client=(
                embedding_client
            ),
            generation_client=(
                generation_client
            ),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

@app.post(
    "/documents",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload and index a document.
    """

    try:

        path = await store_upload(
            file,
        )

        summary = (
            process_uploaded_document(
                path,
            )
        )

        return DocumentUploadResponse(
            status="indexed",
            filename=(
                file.filename
                or path.name
            ),
            summary=summary,
        )

    except HTTPException:
        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "Document indexing error:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document indexing failed."
            ),
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
    )