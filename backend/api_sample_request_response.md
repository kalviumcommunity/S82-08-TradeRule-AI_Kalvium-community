# 3.44 Backend API for the RAG Service

## TradeRule AI

TradeRule AI's RAG pipeline is exposed through a FastAPI backend API so that a frontend, chatbot UI, Postman client, or another service can send a compliance question and receive a grounded answer with source information as structured JSON.

---

# 1. Objective

The objective of this task is to build a backend API that acts as the stable interface between the TradeRule AI RAG pipeline and its consumers.

The API performs the following operations:

1. Accepts a user question through an HTTP request.
2. Validates the incoming request.
3. Sends the question to the existing RAG pipeline.
4. Generates embeddings for the question.
5. Retrieves relevant information from Qdrant.
6. Applies the hallucination guardrail.
7. Generates a grounded answer when sufficient context exists.
8. Validates generated citations.
9. Returns the answer and sources as structured JSON.
10. Returns appropriate HTTP errors when the request or service fails.

---

# 2. API Architecture

```text
                         ┌──────────────────────┐
                         │      Frontend        │
                         │   / Chatbot / App    │
                         └──────────┬───────────┘
                                    │
                                    │ POST /query
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     FastAPI API      │
                         │                      │
                         │ Request Validation   │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   guarded_answer()   │
                         │                      │
                         │ Existing RAG Service │
                         └──────────┬───────────┘
                                    │
                 ┌──────────────────┼──────────────────┐
                 │                  │                  │
                 ▼                  ▼                  ▼
        ┌────────────────┐ ┌────────────────┐ ┌──────────────────┐
        │ Gemini         │ │    Qdrant      │ │ Hallucination    │
        │ Embeddings     │ │ Vector Search  │ │ Guardrail        │
        └────────────────┘ └────────────────┘ └──────────────────┘
                 │                  │                  │
                 └──────────────────┼──────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Grounded Gemini      │
                         │ Answer Generation    │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Citation Validation  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Structured JSON      │
                         │                      │
                         │ answer               │
                         │ sources              │
                         │ status               │
                         │ retrieval metadata   │
                         └──────────────────────┘