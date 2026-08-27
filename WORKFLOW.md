# GitHub Team Workflow

TradeRule AI is a shipment-aware logistics compliance assistant. Development currently spans a Next.js frontend prototype and a FastAPI backend foundation, with the RAG ingestion and retrieval system planned for later implementation.

## 1. Branching Strategy

The `main` branch contains releasable code only.

All new features, fixes, refactoring, and documentation changes are developed on separate branches.

Branch names follow this format:

```text
feature/document-ingestion
feature/compliance-retrieval
fix/citation-display
docs/api-documentation
refactor/retrieval-service
chore/update-dependencies
```

Keep branches focused on one feature, fix, or documentation change. Start from the latest `main` branch before beginning work.

## 2. Local Setup

Required tools:

* Node.js and npm
* Python 3
* Git

Install the frontend dependencies:

```bash
npm ci
```

Create and activate the Python virtual environment on Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create local configuration from the template:

```powershell
Copy-Item .env.example .env
```

Configure the required API, Gemini, Qdrant, and Redis values in `.env` as needed for the work being completed.

Never commit `.env`, API keys, credentials, local document data, `.venv/`, `node_modules/`, or `.next/`.

## 3. Running the Application

Run the FastAPI backend from the repository root with the virtual environment activated:

```powershell
uvicorn backend.src.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`. Verify its foundation with:

```text
http://127.0.0.1:8000/health
```

Run the frontend in a second terminal:

```bash
npm run dev
```

The Next.js application runs at `http://localhost:3000`.

## 4. Development Workflow

1. Create a focused branch from `main`.
2. Make the smallest change that addresses the task.
3. Keep frontend changes in `app/` and `components/`, backend changes in `backend/`, prompt templates in `prompts/`, and local source documents in `data/`.
4. Keep compliance answers grounded in trusted sources and preserve citation and confidence information in user-facing flows.
5. Add or update documentation when setup, configuration, or behavior changes.
6. Run the relevant checks locally before opening a pull request.
7. Push the branch and open a pull request against `main`.

## 5. Validation Checklist

For frontend changes, run:

```bash
npm run lint
npm run build
```

For backend changes, activate `.venv`, start the API, and verify:

```text
GET /health -> {"status":"ok"}
```

For changes involving ingestion or retrieval, also verify document extraction, required metadata, retrieval filtering, citations, and the insufficient-information response. Do not treat an answer as valid when it is not supported by the knowledge base.

Before submitting a pull request, confirm that the frontend and backend can be started from a clean environment using `package-lock.json`, `requirements.txt`, and `.env.example`.

## 6. Pull Requests

Pull requests should include:

* A concise description of the user or system behavior changed.
* The affected area, such as frontend, backend, ingestion, retrieval, or documentation.
* Validation commands that were run and their results.
* Any required environment variables or external services.
* Screenshots for meaningful frontend changes.

Reviewers should check correctness, source grounding, secret handling, setup reproducibility, and whether unrelated files were changed.

## 7. Target RAG Delivery Order

The planned implementation should follow the architecture described in `README.md`:

```text
Documents
	-> Extraction
	-> Cleaning and chunking
	-> Metadata validation
	-> Embeddings
	-> Qdrant storage
	-> Metadata-filtered retrieval
	-> Re-ranking
	-> Grounded generation
	-> Confidence and citations
	-> Next.js API integration
```

Required metadata includes `country`, `document_type`, `carrier`, `product_category`, `effective_date`, `source`, and `page`. Redis caching, evaluation metrics, and hallucination/refusal guards should be added as the corresponding RAG features are implemented.

## 8. Commit and Merge Guidance

Use clear, imperative commit messages, for example:

```text
Add shipment metadata validation
Fix citation display in compliance result
Document local backend setup
```

Keep commits reviewable and avoid mixing formatting-only changes with functional work. Merge only after the pull request has been reviewed and the relevant validation checks pass.