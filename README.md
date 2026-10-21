# TradeRule AI

TradeRule AI is an AI-powered logistics compliance assistant designed to help operations teams determine customs requirements, export and import rules, shipping documentation requirements, and other shipment compliance information.

The application uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from a regulatory knowledge base and generate grounded answers with verifiable source citations.

---

## Project Overview

TradeRule AI combines a Next.js frontend with a FastAPI RAG backend.

The system allows users to:

- Upload compliance documents.
- Extract and clean document content.
- Split documents into token-aware chunks.
- Generate embeddings using Gemini.
- Store embeddings in Qdrant.
- Retrieve semantically relevant content.
- Apply retrieval relevance guardrails.
- Generate grounded answers using Gemini.
- Display source citations.
- Inspect retrieved source text.
- Ask follow-up questions.
- Stream generated answers progressively.
- Cache repeated questions.
- Record structured RAG logs.
- Monitor approximate token usage and cost.
- Generate usage reports.

The overall pipeline is:

```text
Documents
    ↓
Document Loading
    ↓
Text Cleaning
    ↓
Token-Aware Chunking
    ↓
Metadata Tagging
    ↓
Gemini Embeddings
    ↓
Qdrant Vector Database
    ↓
Semantic Retrieval
    ↓
Retrieval Guardrails
    ↓
Context Augmentation
    ↓
Grounded Gemini Generation
    ↓
Citation Validation
    ↓
Next.js Interface
```

---

# Current Project Status

The TradeRule AI Sprint 2 RAG application has progressed from a frontend prototype into a working RAG application.

The implemented system currently includes:

- Shipment intake
- Compliance question interface
- Compliance result interface
- Source citations
- Confidence and retrieval indicators
- Follow-up question support
- Shipment history interface
- Regulations library interface
- Carrier agreements interface
- Audit review interface
- Document upload interface
- Error states
- Insufficient-information states
- Document ingestion
- Text cleaning
- Token-aware chunking
- Metadata tracking
- Gemini embeddings
- Qdrant vector search
- Similarity retrieval
- Metadata filtering
- Retrieval evaluation
- Context augmentation
- Grounded answer generation
- Source citation and attribution
- Hallucination guardrails
- Conversational RAG
- RAG answer evaluation
- FastAPI query API
- Runtime document upload and indexing
- Streaming responses
- Citation source inspection
- Query caching
- Structured logging
- Token and cost monitoring
- Usage reporting

---

# Technology Stack

## Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS
- Next.js App Router

## Backend

- Python
- FastAPI
- Uvicorn
- python-dotenv
- PyMuPDF
- Requests

## AI

- Google Gemini
- Gemini 2.5 Flash for answer generation
- Gemini Embedding model for vector embeddings

## Vector Database

- Qdrant
- Cosine similarity
- Qdrant REST API

## Infrastructure

- Docker
- Git
- GitHub

---

# System Architecture

```text
                         TRADE RULE AI
                              |
                +-------------+-------------+
                |                           |
                v                           v
        Document Upload              User Question
                |                           |
                v                           v
       Document Validation          Query Embedding
                |                           |
                v                           v
       Document Extraction           Qdrant Search
                |                           |
                v                           v
          Text Cleaning                Top-K Results
                |                           |
                v                           v
       Token-Aware Chunking       Retrieval Guardrail
                |                           |
                v                           v
        Metadata Tagging           Context Augmentation
                |                           |
                v                           v
       Gemini Embeddings          Grounded Generation
                |                           |
                v                           v
        Qdrant Vector DB             Citation Validation
                                            |
                           +----------------+----------------+
                           |                |                |
                           v                v                v
                       Citations        Streaming         Caching
                           |                |                |
                           +----------------+----------------+
                                            |
                                            v
                                     Next.js Frontend
                                            |
                           +----------------+----------------+
                           |                                 |
                           v                                 v
                    Structured Logs                    Usage Reports
```

---

# RAG Pipeline

```text
Regulatory / Compliance Documents
            ↓
      Document Loader
            ↓
       Text Cleaner
            ↓
    Token-Aware Chunker
            ↓
      Metadata Tagging
            ↓
     Gemini Embeddings
            ↓
       Qdrant Storage
            ↓
     Semantic Retrieval
            ↓
       Top-K Results
            ↓
   Relevance Guardrails
            ↓
   Context Augmentation
            ↓
    Grounded Prompt
            ↓
    Gemini 2.5 Flash
            ↓
    Citation Validation
            ↓
      Final Answer
```

---

# Document Ingestion Pipeline

Uploaded documents go through:

```text
Upload
   ↓
Filename Validation
   ↓
File Size Validation
   ↓
Safe File Storage
   ↓
Document Extraction
   ↓
Text Cleaning
   ↓
Token-Aware Chunking
   ↓
Metadata Tagging
   ↓
Embedding Generation
   ↓
Qdrant Indexing
```

Supported formats:

```text
.txt
.md
.pdf
```

Newly indexed content becomes available without restarting the backend.

---

# Embeddings

The current embedding model is:

```text
gemini-embedding-001
```

Vector size:

```text
3072 dimensions
```

Similarity metric:

```text
Cosine Similarity
```

---

# Qdrant Vector Database

Default collection:

```text
traderule_rag_chunks
```

Default local URL:

```text
http://localhost:6333
```

TradeRule AI communicates with Qdrant through its REST API.

---

# Retrieval

The user question is embedded and searched against the Qdrant collection.

Current default:

```text
Top-K: 5
```

Retrieved chunks are evaluated by the relevance guardrail before generation.

---

# Retrieval Guardrails

Current configuration:

```text
Minimum top similarity score: 0.72
Minimum supporting chunks: 1
Top-K: 5
```

Weak retrieval produces:

```text
I don't have enough reliable context to answer that.
```

---

# Context Augmentation

Retrieved chunks are injected into the grounded generation prompt.

Current context configuration:

```text
Maximum context tokens: 5000
Reserved instruction tokens: 500
Reserved question tokens: 200
Reserved answer tokens: 1000
```

---

# Grounded Answer Generation

Gemini generates answers using retrieved context.

The prompt instructs the model to:

- Use retrieved context.
- Avoid unsupported external facts.
- Provide concise compliance answers.
- Include citation markers.
- Avoid fabricated sources.
- Refuse when sufficient context is unavailable.

---

# Citation and Source Attribution

Generated answers contain citation markers:

```text
[1]
[2]
[3]
```

Source information includes:

```text
Citation
Document
Chunk ID
Chunk Index
Section
Retrieved Source Text
```

Users can inspect retrieved source text from the frontend.

---

# Citation Validation

Generated citations are validated against retrieved sources.

Invalid citations cause the generated answer to be rejected and the safe fallback response to be returned.

---

# Conversational RAG

Follow-up questions are rewritten into standalone retrieval queries.

Example:

```text
User:
When does an exporter need an export license?

Assistant:
An exporter may require an export license...

User:
What about the destination?
```

Current history budget:

```text
1200 tokens
```

---

# Streaming Responses

Streaming endpoint:

```text
POST /query/stream
```

Supported Server-Sent Events:

```text
citations
token
done
error
```

The frontend progressively displays the answer and citations and handles interrupted streams with retry support.

---

# Caching

Repeated identical queries can be served from an in-memory cache.

Cache keys include:

- Normalized question
- Relevant query settings

Default TTL:

```text
900 seconds
```

Example:

```text
First request
    ↓
Cache MISS
    ↓
RAG pipeline
    ↓
Answer generated
    ↓
Response cached

Same request again
    ↓
Cache HIT
    ↓
Cached response returned
```

---

# Logging

RAG requests are stored as JSON Lines in:

```text
logs/rag_requests.jsonl
```

Records include:

```text
timestamp
request_id
question
answer_preview
sources
cache_hit
input_tokens
output_tokens
estimated_cost
latency_ms
status
error
```

---

# Usage Monitoring

Tracked metrics include:

- Total requests
- Cache hits
- Cache misses
- Cache hit rate
- Input tokens
- Output tokens
- Estimated cost
- Average latency

Generate the report:

```powershell
python backend\src\generate_usage_report.py
```

Output:

```text
logs/usage_summary.json
```

Verified example:

```json
{
  "total_requests": 5,
  "cache_hits": 2,
  "cache_misses": 3,
  "cache_hit_rate": 0.4,
  "total_input_tokens": 144,
  "total_output_tokens": 103,
  "total_estimated_cost": 0.000083,
  "average_latency_ms": 4280.98
}
```

---

# API

## Health Check

```http
GET /health
```

Example:

```json
{
  "status": "ok"
}
```

## Query

```http
POST /query
```

Example request:

```json
{
  "question": "When does an exporter need an export license?"
}
```

## Streaming Query

```http
POST /query/stream
```

Returns:

```text
citations
token
done
error
```

## Document Upload

```http
POST /documents
```

Supported:

```text
.txt
.md
.pdf
```

The endpoint validates, stores, processes, embeds, and indexes the document.

---

# Project Structure

```text
traderule-ai/
│
├── app/
│   ├── admin/
│   ├── agreements/
│   ├── ask/
│   ├── history/
│   ├── library/
│   ├── result/
│   ├── result-error/
│   ├── result-insufficient/
│   └── thread/
│
├── components/
├── public/
│
├── backend/
│   └── src/
│       ├── api.py
│       ├── config.py
│       ├── document_loader.py
│       ├── document_chunker.py
│       ├── text_cleaner.py
│       ├── token_chunker.py
│       ├── chunk_metadata.py
│       ├── batch_embedding.py
│       ├── index_embeddings.py
│       ├── context_augmentation.py
│       ├── citation_attribution.py
│       ├── hallucination_guardrails.py
│       ├── conversational_rag.py
│       ├── rag_evaluation.py
│       ├── streaming_rag.py
│       ├── rag_cache.py
│       ├── rag_logging.py
│       ├── usage_monitoring.py
│       ├── generate_usage_report.py
│       └── test_observability.py
│
├── data/
├── uploads/
├── logs/
│   ├── rag_requests.jsonl
│   └── usage_summary.json
├── prompts/
├── outputs/
├── .env
├── .env.example
├── .gitignore
├── package.json
├── package-lock.json
├── requirements.txt
└── README.md
```

---

# Prerequisites

Install:

- Node.js
- npm
- Python 3
- Git
- Docker Desktop

Verify:

```powershell
node --version
npm --version
python --version
git --version
docker --version
```

---

# Getting Started

## 1. Clone the Repository

```powershell
git clone <repository-url>
cd traderule-ai
```

## 2. Install Frontend Dependencies

```powershell
npm ci
```

## 3. Create Python Virtual Environment

```powershell
python -m venv venv
```

Activate:

```powershell
.\venv\Scripts\Activate.ps1
```

## 4. Install Backend Dependencies

```powershell
pip install -r requirements.txt
```

---

# Environment Configuration

Create `.env`:

```powershell
Copy-Item .env.example .env
```

Configure:

```env
API_BASE_URL=http://localhost:8000

GEMINI_API_KEY=your_gemini_api_key
CHAT_MODEL=gemini-2.5-flash
EMBED_MODEL=

QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

REDIS_URL=redis://localhost:6379

EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
UPLOAD_CHUNK_SIZE=100
UPLOAD_CHUNK_OVERLAP=15
EMBEDDING_BATCH_SIZE=2
COLLECTION_NAME=traderule_rag_chunks

RAG_LOG_DIR=logs
CACHE_TTL_SECONDS=900
```

Frontend `.env.local`:

```env
NEXT_PUBLIC_RAG_API_URL=http://127.0.0.1:8000
```

---

# Secret Management

Never commit:

```text
.env
.env.local
```

Never hardcode:

```text
API keys
Passwords
Private tokens
Cloud credentials
```

Use `.env.example` for documenting required configuration.

For deployment, configure secrets through environment variables in the hosting platform.

---

# Git Ignore

The following should remain excluded:

```text
.env
.env.local
venv/
.venv/
node_modules/
.next/
__pycache__/
*.pyc
```

---

# Qdrant Setup

Start the existing container:

```powershell
docker start traderule-qdrant
```

If it does not exist:

```powershell
docker run -d `
  --name traderule-qdrant `
  -p 6333:6333 `
  -p 6334:6334 `
  qdrant/qdrant
```

Verify:

```powershell
Invoke-WebRequest http://localhost:6333/healthz
```

---

# Running the Backend

```powershell
.\venv\Scripts\Activate.ps1
uvicorn api:app --app-dir backend\src --host 127.0.0.1 --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI:

```text
http://127.0.0.1:8000/openapi.json
```

Health:

```text
http://127.0.0.1:8000/health
```

---

# Running the Frontend

Open another terminal:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Ask interface:

```text
http://localhost:3000/ask
```

---

# End-to-End Usage

```text
1. Start Qdrant
       ↓
2. Start FastAPI
       ↓
3. Start Next.js
       ↓
4. Upload compliance document
       ↓
5. Extract document text
       ↓
6. Clean document
       ↓
7. Create chunks
       ↓
8. Generate embeddings
       ↓
9. Store vectors in Qdrant
       ↓
10. Ask compliance question
       ↓
11. Embed question
       ↓
12. Retrieve relevant chunks
       ↓
13. Apply relevance guardrail
       ↓
14. Inject retrieved context
       ↓
15. Generate grounded answer
       ↓
16. Validate citations
       ↓
17. Display answer and sources
```

---

# End-to-End Example

Question:

```text
When does an exporter need an export license?
```

Grounded answer:

```text
An exporter may require an export license before shipment
for certain controlled products, depending on the product's
destination and classification [1].
```

Primary source:

```text
[1] license_rules.txt
Chunk ID: license-0
Section: export licensing
```

Retrieval details:

```text
Retrieved: 5
Top score: 0.795
Supporting chunks: 2
Threshold: 0.72
Status: answered
```

---

# Upload Example

Example file:

```text
runtime-test-policy.md
```

Example content:

```text
TradeRule AI Runtime Upload Test

A temporary import policy requires importers to verify the
blue customs certificate before submitting a shipment for
clearance.

The blue customs certificate is required for shipments
classified as RT-45 and must be included with the customs
declaration.
```

Upload:

```http
POST /documents
```

Processing:

```text
Stored
  ↓
Extracted
  ↓
Cleaned
  ↓
Chunked
  ↓
Embedded
  ↓
Indexed in Qdrant
  ↓
Available for retrieval
```

---

# Testing

Syntax check:

```powershell
python -m py_compile backend\src\api.py
```

Full observability syntax check:

```powershell
python -m py_compile `
backend\src\rag_cache.py `
backend\src\rag_logging.py `
backend\src\usage_monitoring.py `
backend\src\generate_usage_report.py `
backend\src\test_observability.py `
backend\src\api.py
```

Run observability tests:

```powershell
python backend\src\test_observability.py
```

Expected:

```text
Cache test: PASS
Logging test: PASS
Usage summary test: PASS

ALL 3.48 TESTS COMPLETED
```

---

# Cache Verification

First request:

```text
status:
answered
```

Repeated identical request:

```text
status:
cache_hit
```

Expected cache reason:

```text
Response served from query cache.
```

---

# Error and Safety Handling

## Weak Retrieval

```text
I don't have enough reliable context to answer that.
```

## Invalid Citations

Invalid citations are rejected and the safe fallback is returned.

## Streaming Errors

The UI:

- Preserves partial answer text.
- Preserves retrieved citations.
- Displays an incomplete/error state.
- Allows retry.
- Restores input controls.

## Upload Errors

The upload endpoint handles:

- Unsupported file types
- File size limits
- Empty documents
- Storage failures
- Processing failures
- Indexing failures

---

# RAG Evaluation

The project includes an evaluation dataset and pipeline covering:

- Correctness
- Grounding
- Citation accuracy
- Overall answer quality

---

# Development History

```text
Token and Context Handling
        ↓
Prompt Construction
        ↓
Structured JSON Output
        ↓
Document Loading
        ↓
Text Cleaning
        ↓
Chunking
        ↓
Metadata Tracking
        ↓
Token-Aware Chunking
        ↓
Embedding Generation
        ↓
Embedding Quality Checks
        ↓
Qdrant Setup
        ↓
Vector Indexing
        ↓
Similarity Search
        ↓
Metadata Filtering
        ↓
Retrieval Tuning
        ↓
Retrieval Evaluation
        ↓
RAG Pipeline
        ↓
Context Augmentation
        ↓
Grounded Answer Generation
        ↓
Source Citation
        ↓
Hallucination Guardrails
        ↓
Conversational RAG
        ↓
RAG Evaluation
        ↓
FastAPI API
        ↓
Document Upload
        ↓
Chat Query UI
        ↓
Streaming + Citation Display
        ↓
Caching + Logging + Usage Monitoring
        ↓
Final Delivery
```

---

# Git Branches

Major feature branches:

```text
feature/backend-api
feature/document-upload-indexing
feature/chat-interface-query-ui
feature/streaming-citations
feature/caching-logging-monitoring
```

Latest observability commit:

```text
Add caching logging and usage monitoring
```

---

# Git Development Workflow

```text
GitHub Issue
     ↓
Create Feature Branch
     ↓
Implement Feature
     ↓
Run Tests
     ↓
Commit Changes
     ↓
Push Branch
     ↓
Open Pull Request
     ↓
Code Review
     ↓
Merge
```

---

# Reproducible Setup

```text
Clone repository
       ↓
npm ci
       ↓
Create Python virtual environment
       ↓
Activate virtual environment
       ↓
pip install -r requirements.txt
       ↓
Copy .env.example to .env
       ↓
Configure Gemini API key
       ↓
Start Qdrant
       ↓
Start FastAPI
       ↓
Start Next.js
       ↓
Open application
```

No API keys need to be stored in source code.

---

# Final Delivery Checklist

- [x] Frontend runs
- [x] Backend runs
- [x] Qdrant runs
- [x] Environment configuration documented
- [x] `.env.example` available
- [x] `.env` excluded from Git
- [x] Document upload implemented
- [x] Document ingestion implemented
- [x] Chunking implemented
- [x] Embeddings implemented
- [x] Qdrant indexing implemented
- [x] Semantic retrieval implemented
- [x] Retrieval guardrails implemented
- [x] Grounded generation implemented
- [x] Citation validation implemented
- [x] Conversational follow-ups implemented
- [x] Streaming implemented
- [x] Source inspection implemented
- [x] Caching implemented
- [x] Structured logging implemented
- [x] Usage monitoring implemented
- [x] Usage report implemented
- [x] Observability tests pass
- [ ] Final end-to-end upload demonstration
- [ ] Final Git tag created
- [ ] Final pull request ready
- [ ] Final video recorded

---

# Sprint 2 Final Deliverable

The final Sprint 2 product demonstrates:

```text
Documents
    ↓
Chunks
    ↓
Embeddings
    ↓
Qdrant
    ↓
Retrieval
    ↓
Context
    ↓
Grounded LLM
    ↓
Citations
    ↓
User Interface
```

Additional capabilities:

```text
Streaming
Caching
Logging
Usage Monitoring
Guardrails
Source Inspection
Conversational Follow-ups
```

The goal is to provide compliance answers that are generated from retrieved source information and remain traceable to the underlying evidence.

---

# Security

Never commit:

```text
.env
.env.local
*.pem
```

Never hardcode:

```text
API keys
Passwords
Private tokens
Cloud credentials
```

Use `.env.example` for required configuration.

---

# Known Limitations

- The cache is implemented as an in-memory cache.
- Usage cost is an estimate rather than a billing-system value.
- Local Qdrant is used for development.
- The system depends on the configured Gemini API.
- The compliance knowledge base depends on indexed documents.
- Production-scale background processing and distributed infrastructure require additional deployment work.

---

# Authentication & Role-Based Access Control (RBAC)

TradeRule AI incorporates enterprise-grade authentication and authorization:

### 1. Security Architecture
- **Password Hashing**: Passwords are saved with **Argon2id** (`argon2-cffi`), with memory cost (64 MB), time cost (3 iterations), and 4 parallelism lanes.
- **Session Tokens**: JWT signed via `HS256` using a server-side secret key (`JWT_SECRET`). Tokens expire in 24 hours.
- **Dual Transport**: Supports both HttpOnly, Secure, SameSite cookies (`traderule_session`) and `Authorization: Bearer <token>` headers for cross-origin resilience.
- **Self-Elevation Prevention**: The registration endpoint (`POST /auth/register`) enforces `role: "user"`. Manipulation of payload fields cannot elevate a user to `admin`.
- **RBAC Enforcement**:
  - `user`: Access to compliance RAG queries (`/chat`, `/query`, `/query/stream`), conversation threads (`/thread`), and shipment history (`/history`).
  - `admin`: Exclusive access to document ingestion & upload (`/documents`), document inventory (`/documents/list`), and compliance audit review logs (`/logs`, `/admin/review`).

### 2. Administrator Bootstrap Procedure
TradeRule AI does not use hardcoded administrator credentials. The first administrator account is created via the documented bootstrap utility:

**Command Line Bootstrap:**
```bash
python backend/src/bootstrap_admin.py --email admin@traderule.ai --password "YourStrongPassword123!" --name "Lead Compliance Officer"
```

**Environment Variable Bootstrap:**
In containerized and cloud environments (such as Render), configure the following environment variables. The service will verify whether an admin exists on startup and automatically seed the account:
- `ADMIN_BOOTSTRAP_EMAIL=admin@traderule.ai`
- `ADMIN_BOOTSTRAP_PASSWORD=YourStrongPassword123!`
- `ADMIN_BOOTSTRAP_NAME=TradeRule Administrator`

*Safeguard*: The bootstrap utility detects existing administrators and terminates safely without altering accounts unless the `--force` flag is explicitly provided.

---

# Persistent Storage & Database Configuration

- **User Accounts & Auth**: Managed by SQLAlchemy in `backend/src/db.py`.
  - Development: SQLite at `data/traderule.db` (auto-created).
  - Production: PostgreSQL configured via `DATABASE_URL=postgresql://user:pass@host:5432/dbname`.
- **Vector Embeddings**:
  - Primary: Qdrant Cloud (`QDRANT_URL` and `QDRANT_API_KEY`).
  - Resilient Fallback: Local vector repository `data/embedding_store.json` using exact cosine similarity retrieval if Qdrant Cloud is unreachable or clusters reset.
- **Document Storage**: Uploaded compliance PDFs/texts are stored under `uploads/` with filename sanitization and size guardrails (10MB limit).

---

# Automated Tests & Security Verification

A comprehensive pytest and Next.js validation suite covers authentication, RBAC, and RAG integration:

### 1. Run Automated Backend Tests
```bash
pytest tests/ -v
```
**Test Coverage (12 passed tests):**
- `test_password_hashing_argon2id`: Verifies Argon2id algorithm, salting, and verification.
- `test_registration_and_no_role_elevation`: Ensures public registration cannot assign `admin` role.
- `test_duplicate_registration_rejected`: Enforces unique email constraint (HTTP 409).
- `test_login_success_and_invalid_credentials`: Validates credentials, token generation, and wrong password rejection (HTTP 401).
- `test_unauthenticated_request_rejected`: Verifies protected endpoints reject requests without token/cookie (HTTP 401).
- `test_rbac_user_cannot_access_admin_endpoints`: Confirms regular user is blocked from `/documents` and `/logs` (HTTP 403 Forbidden).
- `test_admin_can_access_admin_endpoints`: Confirms admin accesses `/documents` and `/logs` (HTTP 200).
- `test_logout_clears_cookie`: Ensures `/auth/logout` clears session cookies.
- `test_public_health_endpoint`: Ensures `/health` remains public for monitoring.
- `test_authenticated_rag_query_with_citations`: End-to-end RAG query generating grounded response with citations.
- `test_out_of_domain_query_safe_refusal`: Guardrail test confirming safe refusal on insufficient context.
- `test_document_upload_protection`: Enforces admin-only privileges for PDF/text uploads.

### 2. Run Frontend Production Build Check
```bash
npm run build
```
Compiles all 19 Next.js pages and API routes with zero TypeScript errors.

---

# Production Deployment Guide

### Backend: Render Deployment
1. Connect your repository to [Render](https://render.com).
2. Create a new **Web Service** or use the included `render.yaml` Blueprint.
3. Configure the following build & start settings:
   - **Environment**: Python 3.13
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python backend/src/bootstrap_admin.py && uvicorn api:app --app-dir backend/src --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/health`
4. Set required Environment Variables in the Render Dashboard:
   - `GEMINI_API_KEY`: Your Google Gemini API key.
   - `JWT_SECRET`: Random 64-character secret key.
   - `DATABASE_URL`: PostgreSQL connection string.
   - `ALLOWED_ORIGINS`: `https://your-traderule-frontend.vercel.app,http://localhost:3000`
   - `ADMIN_BOOTSTRAP_EMAIL` & `ADMIN_BOOTSTRAP_PASSWORD`: Initial admin credentials.

### Frontend: Vercel Deployment
1. Import the repository in [Vercel](https://vercel.com).
2. Framework Preset: **Next.js**.
3. Configure Environment Variables:
   - `NEXT_PUBLIC_RAG_API_URL`: Your deployed Render backend URL (e.g., `https://traderule-ai-backend.onrender.com`).
   - `API_BASE_URL`: Your deployed Render backend URL.
4. Deploy the application.

---

# Future Improvements

Potential improvements include:
- Redis-based distributed caching
- Background document ingestion workers (Celery/BullMQ)
- OAuth2 social login (Google, GitHub)
- Multi-tenant organizational isolation
- Production observability dashboards (Datadog, OpenTelemetry)

---

# License

This project is developed as part of TradeRule AI.

