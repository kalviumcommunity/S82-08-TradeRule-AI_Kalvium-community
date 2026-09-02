# TradeRule AI

TradeRule AI is an AI-powered logistics compliance assistant designed to help operations staff determine customs rules, shipping restrictions, required documents, and carrier-specific requirements for a shipment.

The project is being developed as a Retrieval-Augmented Generation (RAG) system. The intended system will retrieve relevant regulatory information from a trusted knowledge base and generate grounded answers with source citations.

## Current Project Status

The current repository contains a Next.js frontend prototype that demonstrates the main TradeRule AI user workflows, including:

* Shipment intake
* Compliance question input
* Compliance results
* Source citations
* Confidence indicators
* Follow-up questions
* Shipment history
* Regulations library
* Carrier agreements
* Audit review
* Document upload interface
* Error and insufficient-information states

The current frontend primarily uses demonstration data and client-side interactions. The complete RAG backend, vector database, AI model integration, and production API layer are not yet implemented.

A FastAPI backend foundation has been added to prepare the project for the backend and RAG implementation described in the project PRD.

## Technology Stack

### Frontend

* Next.js 16.3.1
* React 19.2.8
* TypeScript
* Tailwind CSS
* Next.js App Router

### Backend Foundation

* Python
* FastAPI
* Uvicorn
* python-dotenv
* PyMuPDF
* python-docx
* Qdrant client

### Planned RAG Architecture

The project PRD defines the following target technologies and components:

* FastAPI
* PyMuPDF
* python-docx
* Gemini
* Qdrant
* Redis
* Docker
* GitHub

The target RAG workflow is:

```text
Regulatory Documents
        ↓
Document Extraction
        ↓
Cleaning and Chunking
        ↓
Metadata Tagging
        ↓
Embeddings
        ↓
Qdrant Vector Database
        ↓
Metadata Filtering
        ↓
Semantic Retrieval
        ↓
Re-ranking
        ↓
Grounded Generation
        ↓
Source Citations
        ↓
Next.js Frontend
```

## Project Structure

```text
traderule-ai/
│
├── app/                    # Next.js application routes and pages
├── components/             # Shared React components
├── public/                 # Static frontend assets
│
├── backend/
│   └── src/
│       └── main.py         # FastAPI backend foundation
│
├── data/                   # Local regulatory documents (not committed)
│   └── .gitkeep
│
├── prompts/                # RAG prompt templates
│   └── .gitkeep
│
├── outputs/                # Local outputs and evaluation results
│   └── .gitkeep
│
├── .env                    # Local environment variables (not committed)
├── .env.example            # Environment variable template
├── .gitignore              # Ignored files and local data
├── package.json            # Frontend dependencies and scripts
├── package-lock.json       # Locked frontend dependency versions
├── requirements.txt        # Python backend dependencies
└── README.md               # Project documentation
```

## Prerequisites

Install the following before setting up the project:

* Node.js
* npm
* Python 3
* Git

## Getting Started

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd traderule-ai
```

### 2. Install Frontend Dependencies

Install the dependencies recorded in `package-lock.json`:

```bash
npm ci
```

### 3. Create the Python Virtual Environment

From the project root:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install Backend Dependencies

With the virtual environment activated:

```powershell
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a local `.env` file from the provided example:

```powershell
Copy-Item .env.example .env
```

Open `.env` and provide the required values for the services used by the project.

Example:

```env
# Backend API
API_BASE_URL=http://localhost:8000

# Gemini
GEMINI_API_KEY=
CHAT_MODEL=
EMBED_MODEL=

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=

# Redis
REDIS_URL=redis://localhost:6379
```

Never commit `.env` or real API credentials to Git.

## Running the Backend

Activate the Python virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Start the FastAPI development server:

```powershell
uvicorn backend.src.main:app --reload
```

The backend will be available at:

```text
http://127.0.0.1:8000
```

The current backend foundation provides a health-check endpoint:

```text
http://127.0.0.1:8000/health
```

A successful response is:

```json
{
  "status": "ok"
}
```

## Running the Frontend

Open another terminal in the project root and run:

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

The Next.js application provides the current TradeRule AI prototype interface.

## Environment and Secret Management

API keys and environment-specific configuration must not be hardcoded in application source code.

The project uses:

```text
.env
```

for local environment values.

The `.env` file is excluded from Git.

The repository contains:

```text
.env.example
```

which documents the required environment variables without containing real credentials.

The following local resources are also excluded from version control:

```text
.venv/
node_modules/
.next/
.env
data/
```

The `data/.gitkeep` placeholder is committed so that the required workspace structure remains visible in the repository.

## Reproducible Setup

A teammate can reproduce the development environment from a fresh clone using the following process:

```text
Clone repository
       ↓
npm ci
       ↓
Create Python virtual environment
       ↓
pip install -r requirements.txt
       ↓
Copy .env.example to .env
       ↓
Configure environment variables
       ↓
Start FastAPI backend
       ↓
Start Next.js frontend
```

Frontend dependencies are reproduced using `package-lock.json`.

Python backend dependencies are recorded in `requirements.txt`.

## Clean-Run Verification

The project workspace was verified by:

1. Creating and activating the Python virtual environment.
2. Installing the Python dependencies.
3. Generating `requirements.txt`.
4. Starting the FastAPI backend successfully.
5. Verifying the `/health` endpoint returned HTTP 200.
6. Starting the Next.js development server successfully.
7. Verifying the frontend loaded successfully at `http://localhost:3000`.

The environment can therefore be recreated from the dependency manifests and `.env.example` without relying on the developer's existing local environment.

## TradeRule AI Target Architecture

The project PRD defines the eventual system as a shipment-aware RAG application.

The intended document workflow is:

```text
PDF / DOCX / TXT
       ↓
Text Extraction
       ↓
Cleaning
       ↓
Section/Paragraph-Aware Chunking
       ↓
Required Metadata
       ↓
Embedding Generation
       ↓
Qdrant
```

Required chunk metadata includes:

```text
country
document_type
carrier
product_category
effective_date
source
page
```

The intended retrieval workflow is:

```text
Shipment Details + User Question
              ↓
       Metadata Filtering
              ↓
       Semantic Retrieval
              ↓
           Top-K
              ↓
         Re-ranking
              ↓
       Grounded Generation
              ↓
 Answer + Confidence + Sources
```

The PRD requires answers to be grounded in retrieved context and to explicitly return an insufficient-information response when the knowledge base does not contain enough information.

## Project Goals

The main product goals defined in the PRD include:

* Grounded compliance Q&A
* Source citation and verifiability
* Hallucination guardrails
* Shipment-aware retrieval
* Reduced compliance lookup time
* Conversational follow-up support
* Knowledge-base extensibility
* Auditable answers

## Development Status

### Completed Foundation

* [x] Next.js frontend prototype
* [x] Project dependency configuration
* [x] Python virtual environment
* [x] Python backend dependency manifest
* [x] FastAPI backend foundation
* [x] Backend health-check endpoint
* [x] Structured `data/` directory
* [x] Structured `prompts/` directory
* [x] Structured `outputs/` directory
* [x] `.gitignore` protection
* [x] `.env.example`
* [x] Reproducible setup documentation

### Planned RAG Implementation

* [ ] Document ingestion
* [ ] PDF/DOCX/TXT extraction
* [ ] Metadata validation
* [ ] Section-aware chunking
* [ ] Gemini embedding integration
* [ ] Qdrant vector storage
* [ ] Metadata-filtered retrieval
* [ ] Re-ranking
* [ ] Grounded generation
* [ ] Citation generation
* [ ] Hallucination/refusal guard
* [ ] Redis query caching
* [ ] Frontend-to-backend API integration
* [ ] Evaluation dataset and metrics

## Security

Do not commit:

```text
.env
.venv/
node_modules/
data/
```

Never place API keys or credentials directly in source code.

Use `.env.example` to document required environment variables without exposing secret values.

## License

This project is currently being developed as part of the TradeRule AI project.

## GitHub Development Workflow

TradeRule AI follows an issue-driven development workflow using feature branches, conventional commits, and pull requests.

The standard workflow is:

```text
GitHub Issue
     ↓
Create Feature Branch
     ↓
Implement Changes
     ↓
Run Tests
     ↓
Create Conventional Commits
     ↓
Push Branch
     ↓
Open Pull Request
     ↓
Link GitHub Issue
     ↓
Code Review
     ↓
Approval
     ↓
Merge into main
     ↓
Delete Feature Branch