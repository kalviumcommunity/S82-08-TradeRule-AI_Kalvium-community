# 3.42 Conversational RAG & Follow-Up Context

## Purpose

TradeRule AI must support real conversational questions where later
questions depend on information from earlier turns.

A follow-up such as:

> What about the destination?

is difficult to retrieve accurately on its own because it does not
contain the subject of the conversation.

Conversational RAG solves this by using recent conversation history
to rewrite the follow-up into a standalone retrieval query.

---

## Architecture

```text
Conversation History
        |
        v
Latest User Question
        |
        v
Gemini Query Rewriter
        |
        v
Standalone Retrieval Query
        |
        v
Query Embedding
        |
        v
Qdrant Similarity Search
        |
        v
3.41 Hallucination Guardrail
        |
        +-----------------------------+
        |                             |
        v                             v
Strong Context                 Weak Context
        |                             |
        v                             v
3.40 Citation Pipeline         Safe Refusal
        |
        v
Grounded Answer
        |
        v
Citation Validation
        |
        v
Answer + Sources
        |
        v
Append Turn to History