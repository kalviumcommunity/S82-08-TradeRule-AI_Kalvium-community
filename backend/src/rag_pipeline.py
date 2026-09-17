"""
3.37 RAG Pipeline Architecture & Flow Design

End-to-end Retrieval-Augmented Generation pipeline:

    User Query
        |
        v
    Query Embedding
        |
        v
    Qdrant Retrieval
        |
        v
    Context Assembly
        |
        v
    Gemini Generation
        |
        v
    Answer + Sources

The pipeline keeps each responsibility in a separate,
testable function.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv
from openai import OpenAI
from google import genai


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

load_dotenv()

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
).rstrip("/")

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "traderule_rag_chunks"

EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001",
)

CHAT_MODEL = os.getenv(
    "CHAT_MODEL",
    "gemini-2.5-flash",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEFAULT_TOP_K = 3


# -------------------------------------------------------------------
# Client creation
# -------------------------------------------------------------------

def create_embedding_client() -> OpenAI:
    """
    Create an OpenAI-compatible client for Gemini embeddings.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check the .env file."
        )

    return OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )


def create_generation_client() -> genai.Client:
    """
    Create the native Google GenAI client for answer generation.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check the .env file."
        )

    return genai.Client(
        api_key=GEMINI_API_KEY,
    )


# -------------------------------------------------------------------
# Stage 1: Embed
# -------------------------------------------------------------------

def embed_query(
    client: OpenAI,
    query: str,
) -> list[float]:
    """
    Convert the user's natural-language query into an embedding.
    """

    if not query.strip():
        raise ValueError("Query cannot be empty.")

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )

    return response.data[0].embedding


# -------------------------------------------------------------------
# Stage 2: Retrieve
# -------------------------------------------------------------------

def retrieve_context(
    query_vector: list[float],
    k: int = DEFAULT_TOP_K,
) -> list[dict[str, Any]]:
    """
    Retrieve the top-k relevant chunks from Qdrant.
    """

    if k <= 0:
        raise ValueError("k must be greater than zero.")

    url = (
        f"{QDRANT_URL}/collections/"
        f"{COLLECTION_NAME}/points/search"
    )

    payload = {
        "vector": query_vector,
        "limit": k,
        "with_payload": True,
        "with_vector": False,
    }

    headers = {
        "Content-Type": "application/json",
    }

    if QDRANT_API_KEY:
        headers["api-key"] = QDRANT_API_KEY

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Qdrant retrieval failed.\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

    return response.json().get("result", [])


# -------------------------------------------------------------------
# Payload helpers
# -------------------------------------------------------------------

def get_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Return the Qdrant payload safely."""

    return result.get("payload") or {}


def get_metadata(result: dict[str, Any]) -> dict[str, Any]:
    """Return chunk metadata safely."""

    payload = get_payload(result)

    metadata = payload.get("metadata")

    if isinstance(metadata, dict):
        return metadata

    return {}


def get_chunk_id(result: dict[str, Any]) -> str:
    """Return the stable application chunk ID."""

    payload = get_payload(result)

    chunk_id = payload.get("chunk_id")

    if chunk_id:
        return str(chunk_id)

    return str(result.get("id", "unknown"))


def get_source(result: dict[str, Any]) -> str:
    """Return the source document name."""

    metadata = get_metadata(result)

    source = metadata.get("source")

    if source:
        return str(source)

    payload = get_payload(result)

    source = payload.get("source")

    if source:
        return str(source)

    return "unknown"


def get_text(result: dict[str, Any]) -> str:
    """Return the retrieved chunk text."""

    payload = get_payload(result)

    text = payload.get("text")

    if text:
        return str(text)

    return ""


# -------------------------------------------------------------------
# Stage 3: Context Assembly
# -------------------------------------------------------------------

def assemble_context(
    chunks: list[dict[str, Any]],
) -> str:
    """
    Convert retrieved chunks into a structured context block.

    Each chunk receives a citation number that can be referenced
    by the generated answer.
    """

    if not chunks:
        return ""

    parts = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_id = get_chunk_id(chunk)
        source = get_source(chunk)
        text = get_text(chunk)

        parts.append(
            f"[{index}] Source: {source}\n"
            f"Chunk ID: {chunk_id}\n"
            f"{text}"
        )

    return "\n\n".join(parts)


# -------------------------------------------------------------------
# Stage 4: Generate
# -------------------------------------------------------------------

def build_generation_prompt(
    query: str,
    context: str,
) -> str:
    """
    Build a grounded generation prompt.

    The model is explicitly instructed to use only retrieved
    context and to acknowledge when the context is insufficient.
    """

    return f"""
You are the compliance assistant for TradeRule AI.

Answer the user's question using ONLY the retrieved context below.

Rules:
1. Do not invent facts that are not present in the context.
2. If the context does not contain enough information, clearly say
   that the retrieved information is insufficient.
3. Keep the answer concise and practical.
4. Cite the supporting context using [1], [2], etc.
5. Do not create citations that do not exist.
6. Prefer information directly relevant to the user's question.

Retrieved Context:
------------------
{context}
------------------

User Question:
{query}

Provide a grounded answer with citations.
""".strip()


def generate_answer(
    client: genai.Client,
    query: str,
    context: str,
) -> str:
    """
    Generate a grounded answer using Gemini.
    """

    if not context.strip():
        return (
            "I could not find relevant context for this question. "
            "Please try a more specific compliance query."
        )

    prompt = build_generation_prompt(
        query,
        context,
    )

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
    )

    answer = getattr(response, "text", None)

    if not answer:
        return (
            "The generation model did not return an answer."
        )

    return answer.strip()


# -------------------------------------------------------------------
# Source preparation
# -------------------------------------------------------------------

def build_sources(
    chunks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Prepare source information for the final pipeline response.
    """

    sources = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = get_metadata(chunk)

        sources.append(
            {
                "citation": f"[{index}]",
                "chunk_id": get_chunk_id(chunk),
                "source": get_source(chunk),
                "score": round(
                    float(chunk.get("score", 0.0)),
                    6,
                ),
                "metadata": metadata,
            }
        )

    return sources


# -------------------------------------------------------------------
# Pipeline orchestrator
# -------------------------------------------------------------------

def answer_query(
    query: str,
    k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """
    Execute the complete RAG pipeline.

    Stages:
        1. Embed query
        2. Retrieve chunks
        3. Assemble context
        4. Generate grounded answer
        5. Return answer and sources
    """

    if not query.strip():
        return {
            "query": query,
            "answer": "Please provide a question.",
            "sources": [],
            "retrieved_chunks": 0,
        }

    embedding_client = create_embedding_client()

    generation_client = create_generation_client()

    # ---------------------------------------------------------------
    # Stage 1: Embed
    # ---------------------------------------------------------------

    query_vector = embed_query(
        embedding_client,
        query,
    )

    # ---------------------------------------------------------------
    # Stage 2: Retrieve
    # ---------------------------------------------------------------

    chunks = retrieve_context(
        query_vector,
        k=k,
    )

    # ---------------------------------------------------------------
    # Empty retrieval handling
    # ---------------------------------------------------------------

    if not chunks:
        return {
            "query": query,
            "answer": (
                "I could not find relevant context for this question. "
                "Please try a more specific compliance query."
            ),
            "sources": [],
            "retrieved_chunks": 0,
        }

    # ---------------------------------------------------------------
    # Stage 3: Assemble context
    # ---------------------------------------------------------------

    context = assemble_context(chunks)

    # ---------------------------------------------------------------
    # Stage 4: Generate answer
    # ---------------------------------------------------------------

    answer = generate_answer(
        generation_client,
        query,
        context,
    )

    # ---------------------------------------------------------------
    # Stage 5: Return answer + sources
    # ---------------------------------------------------------------

    sources = build_sources(chunks)

    return {
        "query": query,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": len(chunks),
    }


# -------------------------------------------------------------------
# Display helpers
# -------------------------------------------------------------------

def print_pipeline_flow() -> None:
    """Print the pipeline architecture."""

    print()
    print("RAG PIPELINE")
    print("=" * 70)
    print("User Query")
    print("    |")
    print("    v")
    print("Query Embedding")
    print("    |")
    print("    v")
    print("Qdrant Vector Retrieval")
    print("    |")
    print("    v")
    print("Context Assembly")
    print("    |")
    print("    v")
    print("Gemini Grounded Generation")
    print("    |")
    print("    v")
    print("Answer + Sources")
    print("=" * 70)
    print()


def print_result(
    result: dict[str, Any],
) -> None:
    """Print the final pipeline result."""

    print()
    print("=" * 70)
    print("END-TO-END RAG RESULT")
    print("=" * 70)

    print()
    print("USER QUERY")
    print("-" * 70)
    print(result["query"])

    print()
    print("GENERATED ANSWER")
    print("-" * 70)
    print(result["answer"])

    print()
    print("RETRIEVED SOURCES")
    print("-" * 70)

    if not result["sources"]:
        print("No sources retrieved.")
    else:
        for source in result["sources"]:
            print(
                f"{source['citation']} "
                f"{source['source']} | "
                f"chunk={source['chunk_id']} | "
                f"score={source['score']:.6f}"
            )

    print()
    print(
        f"Retrieved chunks: "
        f"{result['retrieved_chunks']}"
    )

    print("=" * 70)
    print()


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> None:
    """
    Run an end-to-end sample RAG query.
    """

    sample_query = (
        "When does an exporter need an export license?"
    )

    print()
    print("=" * 70)
    print("3.37 RAG PIPELINE ARCHITECTURE & FLOW DESIGN")
    print("=" * 70)

    print_pipeline_flow()

    print("Pipeline configuration")
    print("-" * 70)
    print(f"Embedding model : {EMBEDDING_MODEL}")
    print(f"Chat model      : {CHAT_MODEL}")
    print(f"Qdrant          : {QDRANT_URL}")
    print(f"Collection      : {COLLECTION_NAME}")
    print(f"Top-K           : {DEFAULT_TOP_K}")

    print()
    print("Running sample query...")
    print(f"Query: {sample_query}")

    result = answer_query(
        sample_query,
        k=DEFAULT_TOP_K,
    )

    print_result(result)


if __name__ == "__main__":
    main()