# TradeRule AI — Context Injection & Prompt Augmentation

## Overview

Context injection is the stage of the RAG pipeline where retrieved
chunks are transformed into structured evidence and inserted into the
generation prompt.

The goal is to provide the model with relevant evidence, source
markers, and explicit grounding instructions while staying within the
available token budget.

## Flow

```text
User Query
    |
    v
Query Embedding
    |
    v
Qdrant Retrieval
    |
    v
Retrieved Chunks
    |
    v
Format Chunks
    |
    v
Add Source Markers
    |
    v
Count Tokens
    |
    v
Apply Context Token Budget
    |
    v
Assemble Context
    |
    v
Build Grounded Prompt
    |
    v
Generation Model