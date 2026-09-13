"""
3.46 Chat Interface & Query UI
TradeRule AI RAG Backend API

Endpoints:

    GET  /health
    POST /query
    POST /documents
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv

# ============================================================
# MODULE PATH
# ============================================================

SRC_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


# ============================================================
# ENVIRONMENT
# ============================================================

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

from fastapi.middleware.cors import CORSMiddleware

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
# REQUEST MODELS
# ============================================================

class QueryRequest(BaseModel):
    """
    Request body for /query.
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
# QUERY RESPONSE MODELS
# ============================================================

class Source(BaseModel):
    """
    Retrieved source metadata.
    """

    citation: str
    source: str | None = None
    chunk_id: str | None = None
    chunk_index: Any = None


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
    Structured response returned after
    successful document indexing.
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
# CLIENT INITIALIZATION
# ============================================================

def initialize_clients() -> None:
    """
    Initialize embedding and generation clients.
    """

    global embedding_client
    global generation_client

    embedding_client = create_embedding_client()

    generation_client = create_generation_client()


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
# HEALTH ENDPOINT
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check() -> HealthResponse:
    """
    Check whether the API is running.
    """

    return HealthResponse(
        status="ok",
        service=API_TITLE,
        version=API_VERSION,
    )


# ============================================================
# QUERY ENDPOINT
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
    """

    # --------------------------------------------------------
    # CLIENT VALIDATION
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # REQUEST VALIDATION
    # --------------------------------------------------------

    try:

        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Question cannot be empty."
                ),
            )

        # ----------------------------------------------------
        # GUARDED RAG
        # ----------------------------------------------------

        result = guarded_answer(
            question=question,
            embedding_client=embedding_client,
            generation_client=generation_client,
            k=TOP_K,
        )

        # ----------------------------------------------------
        # SOURCE SERIALIZATION
        # ----------------------------------------------------

        sources = []

        for source in result.sources:

            sources.append(
                Source(
                    citation=str(
                        source.get(
                            "citation",
                            "",
                        )
                    ),
                    source=(
                        str(
                            source["source"]
                        )
                        if source.get(
                            "source"
                        ) is not None
                        else None
                    ),
                    chunk_id=(
                        str(
                            source["chunk_id"]
                        )
                        if source.get(
                            "chunk_id"
                        ) is not None
                        else None
                    ),
                    chunk_index=source.get(
                        "chunk_index"
                    ),
                )
            )

        # ----------------------------------------------------
        # STRUCTURED RESPONSE
        # ----------------------------------------------------

        return QueryResponse(
            answer=result.answer,
            sources=sources,
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

    # --------------------------------------------------------
    # KNOWN HTTP ERRORS
    # --------------------------------------------------------

    except HTTPException:
        raise

    # --------------------------------------------------------
    # VALIDATION ERRORS
    # --------------------------------------------------------

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # --------------------------------------------------------
    # UNEXPECTED ERRORS
    # --------------------------------------------------------

    except Exception as error:

        print(
            f"RAG API error: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail="RAG service failed.",
        )


# ============================================================
# DOCUMENT UPLOAD ENDPOINT
# ============================================================

@app.post(
    "/documents",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Upload a document and index it into
    the existing RAG knowledge base.

    Pipeline:

        validate
          ↓
        store
          ↓
        load
          ↓
        clean
          ↓
        chunk
          ↓
        metadata
          ↓
        embed
          ↓
        Qdrant
    """

    try:

        # ----------------------------------------------------
        # STORE AND VALIDATE
        # ----------------------------------------------------

        path = await store_upload(
            file,
        )

        # ----------------------------------------------------
        # PROCESS DOCUMENT
        # ----------------------------------------------------

        summary = process_uploaded_document(
            path,
        )

        # ----------------------------------------------------
        # SUCCESS RESPONSE
        # ----------------------------------------------------

        return DocumentUploadResponse(
            status="indexed",
            filename=(
                file.filename
                or path.name
            ),
            summary=summary,
        )

    # --------------------------------------------------------
    # EXPECTED CLIENT ERRORS
    # --------------------------------------------------------

    except HTTPException:
        raise

    # --------------------------------------------------------
    # VALIDATION ERRORS
    # --------------------------------------------------------

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    # --------------------------------------------------------
    # UNEXPECTED PROCESSING ERRORS
    # --------------------------------------------------------

    except Exception as error:

        print(
            f"Document indexing error: "
            f"{error}"
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