# TradeRule AI — Product Requirements Document

## 1. Product Overview

TradeRule AI is a Retrieval-Augmented Generation (RAG) application designed to help users understand international shipment and trade compliance requirements.

The system allows users to upload compliance documents, process and index their contents, and ask natural-language questions. The application retrieves relevant information from the indexed knowledge base and generates grounded answers with source citations.

## 2. Problem Statement

International shipment and trade compliance involves multiple rules, documentation requirements, licensing requirements, and import/export restrictions.

Users may need to search across multiple compliance documents to determine what rules apply to a shipment. Traditional document search can require manually reading several documents and identifying relevant sections.

TradeRule AI provides a question-answering interface that retrieves relevant compliance information and presents a grounded response together with the sources used to generate the answer.

## 3. Target Users

The primary users are:

- Exporters
- Importers
- Logistics and shipping teams
- Trade compliance teams
- Operations teams
- Users who need to understand shipment documentation and compliance requirements

## 4. Knowledge Source

The application uses a curated shipment and trade compliance document corpus.

Example knowledge sources include:

- Customs requirements
- Export guidelines
- Import rules
- Shipping documentation requirements
- Export licensing rules

Documents are processed, cleaned, chunked, embedded, and indexed in a vector database.

## 5. Product Goals

The product should:

1. Allow users to upload supported compliance documents.
2. Process documents automatically.
3. Split documents into retrieval-friendly chunks.
4. Generate embeddings for document chunks.
5. Store embeddings and metadata in a vector database.
6. Retrieve relevant context for user questions.
7. Generate answers grounded in retrieved context.
8. Display source citations.
9. Prevent unsupported answers when retrieval confidence is insufficient.
10. Provide a simple interface for asking compliance questions.

## 6. Functional Requirements

### Document Upload

The system must:

- Accept supported document formats.
- Validate uploaded files.
- Safely store uploaded documents.
- Extract document text.
- Clean extracted text.
- Create token-aware chunks.
- Generate embeddings.
- Index chunks in Qdrant.

### Question Answering

The system must:

- Accept natural-language questions.
- Generate an embedding for the question.
- Retrieve relevant document chunks.
- Evaluate retrieval relevance.
- Inject retrieved context into the generation prompt.
- Generate a grounded response.
- Return source citations.

### Citation Verification

The system must identify the sources used by the generated answer.

Citations should allow users to determine which retrieved document and chunk support the response.

### Hallucination Protection

If retrieved context does not meet the required relevance threshold, the system should refuse to provide an unsupported answer.

The application should prefer a clear insufficient-context response rather than inventing information.

## 7. RAG Architecture

```text
Documents
    ↓
Document Extraction
    ↓
Text Cleaning
    ↓
Token-Aware Chunking
    ↓
Gemini Embeddings
    ↓
Qdrant Vector Database
    ↓
Question
    ↓
Query Embedding
    ↓
Similarity Retrieval
    ↓
Retrieval Guardrails
    ↓
Context Augmentation
    ↓
Gemini Grounded Generation
    ↓
Citation Validation
    ↓
Answer + Sources
```

## 8. Embedding and Vector Database

The application uses Gemini embeddings to represent documents and user questions as vectors.

Qdrant is used as the vector database for storing document embeddings and associated metadata.

Similarity search is used to retrieve the most relevant chunks for a question.

## 9. User Experience

The user should be able to:

1. Access the TradeRule AI interface.
2. Provide shipment context.
3. Ask a compliance question.
4. See a grounded answer.
5. See citations associated with the answer.
6. Inspect retrieved source evidence.

## 10. Non-Functional Requirements

### Reproducibility

Another developer should be able to clone the repository, configure environment variables, install dependencies, start Qdrant, run the backend and frontend, and use the application.

### Security

API keys and other secrets must not be hardcoded or committed to the repository.

Environment variables should be used for sensitive configuration.

### Reliability

The system should handle:

- Invalid uploads
- Unsupported document formats
- Empty documents
- Processing errors
- Weak retrieval context
- Invalid citations
- API errors

### Observability

The application should provide logging and usage monitoring for RAG requests.

## 11. Success Criteria

The application is successful when:

- A supported document can be uploaded and indexed.
- Indexed content can be retrieved through semantic search.
- Users can ask questions through the application.
- Answers are grounded in retrieved documents.
- Citations identify the supporting sources.
- Weak retrieval results produce a safe refusal.
- The complete workflow can be reproduced using the README.

## 12. Current Scope

The Sprint 2 implementation includes:

- Document ingestion
- Chunking
- Embeddings
- Qdrant indexing
- Similarity retrieval
- Context augmentation
- Grounded generation
- Source citations
- Hallucination guardrails
- Conversational RAG
- Streaming responses
- Caching
- Logging
- Usage monitoring
- Frontend query interface

## 13. Future Improvements

Potential future improvements include:

- More advanced document formats
- Improved retrieval and reranking
- Production-grade persistent caching
- Authentication and role-based access
- More comprehensive compliance datasets
- Deployment to cloud infrastructure
- Advanced analytics and monitoring
- More detailed shipment-specific reasoning

## 14. Product Outcome

TradeRule AI transforms compliance documents into a searchable knowledge base and provides a grounded question-answering interface that connects generated answers to their source evidence.

The goal is to make compliance information easier to retrieve, understand, and verify.
