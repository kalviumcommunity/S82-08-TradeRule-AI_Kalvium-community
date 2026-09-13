# TradeRule AI — RAG Pipeline Flow

## Overview

TradeRule AI uses a Retrieval-Augmented Generation pipeline to answer
international shipment compliance questions using retrieved regulatory
and compliance documents.

## End-to-End Flow

```text
User Query
    |
    v
Query Embedding
    |
    | Gemini Embedding Model
    v
Vector Representation
    |
    v
Qdrant Vector Search
    |
    | Top-K relevant chunks
    v
Retrieved Chunks
    |
    v
Context Assembly
    |
    | Source + chunk ID + text
    v
Grounded Prompt
    |
    v
Gemini Generation
    |
    v
Grounded Answer
    |
    +----> Retrieved Sources