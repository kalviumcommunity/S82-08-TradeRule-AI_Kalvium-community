"""
3.48 Caching, Logging & Usage Monitoring
TradeRule AI RAG Backend API
"""

from __future__ import annotations

import os
import sys
import time
import uuid
import json
from pathlib import Path
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
    Depends,
    Response,
    status,
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
from sqlalchemy.orm import Session

try:
    from .db import init_db, get_db, User, get_user_by_email, create_user
    from .auth import (
        get_current_user,
        require_admin,
        hash_password,
        verify_password,
        create_access_token,
        set_auth_cookie,
        clear_auth_cookie,
        validate_email_address,
        validate_password_strength,
    )
except ImportError:
    from db import init_db, get_db, User, get_user_by_email, create_user
    from auth import (
        get_current_user,
        require_admin,
        hash_password,
        verify_password,
        create_access_token,
        set_auth_cookie,
        clear_auth_cookie,
        validate_email_address,
        validate_password_strength,
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
    "0.0.0.0",
)

API_PORT = int(
    os.getenv(
        "PORT",
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
# AUTHENTICATION MODELS
# ============================================================

class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    full_name: str = Field(default="", description="User full name")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class AuthUserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    created_at: str | None = None


class AuthResponse(BaseModel):
    status: str = "ok"
    user: AuthUserResponse
    token: str


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
    Initialize DB schema and RAG clients when the API starts.
    """

    init_db()
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

allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
custom_origins = os.getenv("ALLOWED_ORIGINS")
if custom_origins:
    for origin in custom_origins.split(","):
        origin = origin.strip()
        if origin and origin not in allowed_origins:
            allowed_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
# AUTHENTICATION ENDPOINTS
# ============================================================

@app.post(
    "/auth/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user account.
    Role is strictly enforced as 'user' for public registration.
    """
    email = validate_email_address(payload.email)
    validate_password_strength(payload.password)

    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    pwd_hash = hash_password(payload.password)
    user = create_user(
        db=db,
        email=email,
        password_hash=pwd_hash,
        full_name=payload.full_name,
        role="user",
    )

    token = create_access_token(user)
    set_auth_cookie(response, token)

    return AuthResponse(
        status="ok",
        user=AuthUserResponse(**user.to_dict()),
        token=token,
    )


@app.post(
    "/auth/login",
    response_model=AuthResponse,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate user and create session cookie + token.
    """
    email = payload.email.strip().lower()
    user = get_user_by_email(db, email)

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    token = create_access_token(user)
    set_auth_cookie(response, token)

    return AuthResponse(
        status="ok",
        user=AuthUserResponse(**user.to_dict()),
        token=token,
    )


@app.get(
    "/auth/me",
    response_model=AuthUserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
) -> AuthUserResponse:
    """
    Get details of currently authenticated user.
    """
    return AuthUserResponse(**current_user.to_dict())


@app.post(
    "/auth/logout",
)
def logout(
    response: Response,
) -> dict[str, str]:
    """
    Clear session cookie and log out.
    """
    clear_auth_cookie(response)
    return {"status": "ok", "message": "Logged out successfully."}


# ============================================================
# NORMAL QUERY
# ============================================================

@app.post(
    "/query",
    response_model=QueryResponse,
)
def query_rag(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    admin_user: User = Depends(require_admin),
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
# CHAT ENDPOINT (COMPATIBILITY)
# ============================================================

class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Direct chat endpoint compatible with frontend chat route.
    """
    query_req = QueryRequest(question=request.question)
    resp = query_rag(query_req, current_user=current_user)
    return {
        "answer": resp.answer,
        "sources": [source.model_dump() for source in resp.sources],
        "status": resp.status,
        "top_score": resp.top_score,
        "retrieval_count": resp.retrieval_count,
        "supporting_chunks": resp.supporting_chunks,
        "threshold": resp.threshold,
        "reason": resp.reason,
    }


# ============================================================
# AUDIT LOGS ENDPOINT
# ============================================================

@app.get("/logs")
def get_logs(
    limit: int = 50,
    admin_user: User = Depends(require_admin),
) -> list[dict[str, Any]]:
    """
    Return recent RAG request audit logs for the admin review page.
    """
    log_file = Path(SRC_DIR).parent.parent / "logs" / "rag_requests.jsonl"
    if not log_file.exists():
        log_file = Path("logs/rag_requests.jsonl")

    if not log_file.exists():
        return []

    records = []
    try:
        with log_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except Exception:
                        continue
    except Exception as e:
        print(f"Error reading logs: {e}")
        return []

    return records[-limit:][::-1]


# ============================================================
# DOCUMENTS LIST ENDPOINT
# ============================================================

@app.get("/documents/list")
def list_documents(
    admin_user: User = Depends(require_admin),
) -> list[dict[str, Any]]:
    """
    Return list of indexed regulatory documents.
    """
    docs = [
        {"filename": "IMDG_Code_Amendment_41-22.pdf", "upload_date": "2026-06-12", "status": "Indexed"},
        {"filename": "SOLAS_Chapter_VII_Carriage_of_Dangerous_Goods.pdf", "upload_date": "2026-06-11", "status": "Indexed"},
        {"filename": "CBP_Customs_Bulletin_Vol60.pdf", "upload_date": "2026-06-10", "status": "Indexed"},
        {"filename": "Carrier_Agreements_and_Routing_Guide.md", "upload_date": "2026-06-08", "status": "Indexed"},
        {"filename": "Industrial_Chemicals_Transit_Compliance.md", "upload_date": "2026-06-06", "status": "Indexed"},
        {"filename": "TradeRule_AI_System_Guide.md", "upload_date": "2026-06-05", "status": "Indexed"},
        {"filename": "Textile_Quotas_and_Tariff_Classification_Guide.md", "upload_date": "2026-06-04", "status": "Indexed"},
        {"filename": "customs_requirements.txt", "upload_date": "2026-06-01", "status": "Indexed"},
        {"filename": "export_guidelines.md", "upload_date": "2026-06-01", "status": "Indexed"},
    ]

    upload_dir = Path(SRC_DIR).parent.parent / "uploads"
    if upload_dir.exists():
        for f in upload_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                docs.insert(0, {
                    "filename": f.name,
                    "upload_date": time.strftime("%Y-%m-%d", time.localtime(f.stat().st_mtime)),
                    "status": "Indexed",
                })

    return docs


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