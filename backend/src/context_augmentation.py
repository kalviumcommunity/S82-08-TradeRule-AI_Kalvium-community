"""
3.38 Context Injection & Prompt Augmentation

TradeRule AI RAG context assembly pipeline:

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
Build Grounded Augmented Prompt

Assignment requirements covered:
1. Inject retrieved chunks into a prompt.
2. Enforce a token budget.
3. Add [1], [2], ... source markers.
4. Instruct the model to answer only from context.
5. Save a sample augmented prompt and token-budget result.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI


# ===================================================================
# CONFIGURATION
# ===================================================================

load_dotenv()

QDRANT_URL = os.getenv(
    "QDRANT_URL",
    "http://localhost:6333",
).rstrip("/")

COLLECTION_NAME = "traderule_rag_chunks"

EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------------------------------------------------------
# Prompt token budget
# ---------------------------------------------------------------
#
# Total prompt budget:
#   5000 tokens
#
# Reserved for:
#   Instructions = 500
#   Question     = 200
#   Answer       = 1000
#
# Available for retrieved context:
#   5000 - 500 - 200 - 1000 = 3300
# ---------------------------------------------------------------

MAX_CONTEXT_TOKENS = 5000

RESERVED_INSTRUCTION_TOKENS = 500
RESERVED_QUESTION_TOKENS = 200
RESERVED_ANSWER_TOKENS = 1000

TOP_K = 5

TOKEN_ENCODING = "cl100k_base"


# ===================================================================
# TOKEN COUNTING
# ===================================================================

def get_tokenizer():
    """
    Return the tokenizer used for context token estimation.
    """

    return tiktoken.get_encoding(TOKEN_ENCODING)


def count_tokens(text: str) -> int:
    """
    Count tokens in the supplied text.
    """

    tokenizer = get_tokenizer()

    return len(
        tokenizer.encode(
            text,
            disallowed_special=(),
        )
    )


def get_available_context_budget() -> int:
    """
    Calculate how many tokens can be used by retrieved context.

    Space is reserved for:
    - grounding instructions
    - user question
    - model answer
    """

    available = (
        MAX_CONTEXT_TOKENS
        - RESERVED_INSTRUCTION_TOKENS
        - RESERVED_QUESTION_TOKENS
        - RESERVED_ANSWER_TOKENS
    )

    return max(available, 0)


# ===================================================================
# EMBEDDING CLIENT
# ===================================================================

def create_embedding_client() -> OpenAI:
    """
    Create the OpenAI-compatible Gemini embedding client.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check your .env file."
        )

    return OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=EMBEDDING_BASE_URL,
    )


# ===================================================================
# QUERY EMBEDDING
# ===================================================================

def embed_query(
    client: OpenAI,
    query: str,
) -> list[float]:
    """
    Convert the user query into an embedding vector.
    """

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )

    return response.data[0].embedding


# ===================================================================
# QDRANT RETRIEVAL
# ===================================================================

def retrieve_chunks(
    query_vector: list[float],
    k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Retrieve the top-k chunks from Qdrant.
    """

    if k <= 0:
        raise ValueError(
            "k must be greater than zero."
        )

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

    response = requests.post(
        url,
        json=payload,
        timeout=60,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Qdrant retrieval failed.\n"
            f"Status: {response.status_code}\n"
            f"Response: {response.text}"
        )

    return response.json().get(
        "result",
        [],
    )


# ===================================================================
# QDRANT PAYLOAD HELPERS
# ===================================================================

def get_payload(
    chunk: dict[str, Any],
) -> dict[str, Any]:
    """
    Safely retrieve the Qdrant payload.
    """

    payload = chunk.get("payload")

    if isinstance(payload, dict):
        return payload

    return {}


def get_metadata(
    chunk: dict[str, Any],
) -> dict[str, Any]:
    """
    Safely retrieve metadata from the Qdrant payload.
    """

    payload = get_payload(chunk)

    metadata = payload.get("metadata")

    if isinstance(metadata, dict):
        return metadata

    return {}


def get_chunk_id(
    chunk: dict[str, Any],
) -> str:
    """
    Retrieve the stable application chunk ID.
    """

    payload = get_payload(chunk)

    chunk_id = payload.get("chunk_id")

    if chunk_id:
        return str(chunk_id)

    return str(
        chunk.get(
            "id",
            "unknown",
        )
    )


def get_source(
    chunk: dict[str, Any],
) -> str:
    """
    Retrieve the source document name.
    """

    metadata = get_metadata(chunk)

    source = metadata.get("source")

    if source:
        return str(source)

    payload = get_payload(chunk)

    source = payload.get("source")

    if source:
        return str(source)

    return "unknown"


def get_chunk_index(
    chunk: dict[str, Any],
) -> Any:
    """
    Retrieve the chunk index from metadata.
    """

    metadata = get_metadata(chunk)

    return metadata.get(
        "chunk_index",
        "unknown",
    )


def get_text(
    chunk: dict[str, Any],
) -> str:
    """
    Retrieve chunk text.
    """

    payload = get_payload(chunk)

    text = payload.get("text")

    if text is None:
        return ""

    return str(text)


# ===================================================================
# TASK 1 + TASK 3
# FORMAT CHUNKS + SOURCE MARKERS
# ===================================================================

def format_chunk(
    index: int,
    chunk: dict[str, Any],
) -> str:
    """
    Format a retrieved chunk with a source marker.

    Example:

    [1] Source: license_rules.txt#0
    Chunk ID: license-0
    <chunk text>
    """

    source = get_source(chunk)

    chunk_index = get_chunk_index(chunk)

    chunk_id = get_chunk_id(chunk)

    text = get_text(chunk)

    marker = (
        f"[{index}] "
        f"Source: {source}#{chunk_index}"
    )

    return (
        f"{marker}\n"
        f"Chunk ID: {chunk_id}\n"
        f"{text}"
    )


# ===================================================================
# TASK 2
# TOKEN-BUDGET CONTROL
# ===================================================================

def assemble_context(
    chunks: list[dict[str, Any]],
) -> tuple[
    str,
    int,
    list[dict[str, Any]],
    bool,
]:
    """
    Assemble retrieved chunks without exceeding the context budget.

    Higher-ranked chunks are considered first.

    Returns:

        context
        token_count
        selected_chunks
        budget_limit_reached
    """

    selected_chunks = []

    formatted_parts = []

    used_tokens = 0

    available_budget = (
        get_available_context_budget()
    )

    budget_limit_reached = False

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        formatted = format_chunk(
            index,
            chunk,
        )

        chunk_tokens = count_tokens(
            formatted
        )

        separator_tokens = 0

        if formatted_parts:
            separator_tokens = count_tokens(
                "\n\n---\n\n"
            )

        required_tokens = (
            chunk_tokens
            + separator_tokens
        )

        # -----------------------------------------------------------
        # Stop if adding this chunk would exceed the budget.
        # -----------------------------------------------------------

        if (
            used_tokens + required_tokens
            > available_budget
        ):
            budget_limit_reached = True
            break

        formatted_parts.append(
            formatted
        )

        selected_chunks.append(
            chunk
        )

        used_tokens += required_tokens

    context = "\n\n---\n\n".join(
        formatted_parts
    )

    return (
        context,
        used_tokens,
        selected_chunks,
        budget_limit_reached,
    )


# ===================================================================
# TASK 4
# GROUNDED PROMPT
# ===================================================================

def build_augmented_prompt(
    question: str,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build the grounded augmented prompt.

    The prompt clearly separates:
    - instructions
    - retrieved context
    - question
    - answer
    """

    (
        context,
        context_tokens,
        selected_chunks,
        budget_limit_reached,
    ) = assemble_context(chunks)

    available_budget = (
        get_available_context_budget()
    )

    # ---------------------------------------------------------------
    # Handle empty context.
    # ---------------------------------------------------------------

    if not context.strip():

        prompt = f"""
You are a grounded compliance assistant for TradeRule AI.

Answer the question using ONLY the provided context.

If the provided context does not contain enough information, say:

"I don't have enough information in the provided context."

Do not use unsupported external knowledge.

Context:
[No relevant context was selected.]

Question:
{question}

Answer:
""".strip()

        return {
            "prompt": prompt,
            "context_tokens": 0,
            "available_context_tokens": available_budget,
            "selected_chunks": [],
            "sources_used": [],
            "budget_limit_reached": budget_limit_reached,
        }

    # ---------------------------------------------------------------
    # Build grounded prompt.
    # ---------------------------------------------------------------

    prompt = f"""
You are a grounded compliance assistant for TradeRule AI.

Answer the user's question using ONLY the provided context.

GROUNDING INSTRUCTIONS:
1. Use only information contained in the retrieved context.
2. Do not invent facts that are not present in the context.
3. Do not rely on outside knowledge.
4. If the context does not contain enough information, say:
   "I don't have enough information in the provided context."
5. Cite supporting evidence using the source markers [1], [2],
   [3], etc.
6. Only use citation markers that actually exist in the context.
7. Keep the answer concise and practical.

RETRIEVED CONTEXT:
------------------------------------------------------------------
{context}
------------------------------------------------------------------

QUESTION:
{question}

ANSWER:
""".strip()

    # ---------------------------------------------------------------
    # Prepare source information.
    # ---------------------------------------------------------------

    sources_used = []

    for index, chunk in enumerate(
        selected_chunks,
        start=1,
    ):
        sources_used.append(
            {
                "citation": f"[{index}]",
                "source": get_source(chunk),
                "chunk_id": get_chunk_id(chunk),
                "chunk_index": get_chunk_index(
                    chunk
                ),
            }
        )

    return {
        "prompt": prompt,
        "context_tokens": context_tokens,
        "available_context_tokens": available_budget,
        "selected_chunks": selected_chunks,
        "sources_used": sources_used,
        "budget_limit_reached": budget_limit_reached,
    }


# ===================================================================
# DISPLAY — RETRIEVED CHUNKS
# ===================================================================

def print_retrieved_chunks(
    chunks: list[dict[str, Any]],
) -> None:
    """
    Display the retrieved chunks before context assembly.
    """

    print()
    print("RETRIEVED CHUNKS")
    print("-" * 70)

    if not chunks:
        print("No chunks retrieved.")
        return

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        score = float(
            chunk.get(
                "score",
                0.0,
            )
        )

        print(
            f"[{index}] "
            f"{get_source(chunk)} | "
            f"chunk={get_chunk_id(chunk)} | "
            f"score={score:.6f}"
        )


# ===================================================================
# DISPLAY — TOKEN BUDGET
# ===================================================================

def print_budget_report(
    result: dict[str, Any],
    retrieved_count: int,
) -> None:
    """
    Display token-budget information.
    """

    print()
    print("TOKEN BUDGET")
    print("-" * 70)

    print(
        f"Maximum prompt budget : "
        f"{MAX_CONTEXT_TOKENS}"
    )

    print(
        f"Reserved instructions : "
        f"{RESERVED_INSTRUCTION_TOKENS}"
    )

    print(
        f"Reserved question     : "
        f"{RESERVED_QUESTION_TOKENS}"
    )

    print(
        f"Reserved answer       : "
        f"{RESERVED_ANSWER_TOKENS}"
    )

    print(
        f"Available context     : "
        f"{result['available_context_tokens']}"
    )

    print(
        f"Context tokens used   : "
        f"{result['context_tokens']}"
    )

    print(
        f"Chunks retrieved      : "
        f"{retrieved_count}"
    )

    print(
        f"Chunks selected       : "
        f"{len(result['selected_chunks'])}"
    )

    print(
        f"Budget limit reached  : "
        f"{result['budget_limit_reached']}"
    )


# ===================================================================
# DISPLAY — SOURCES
# ===================================================================

def print_sources(
    result: dict[str, Any],
) -> None:
    """
    Display sources that were actually injected into the prompt.
    """

    print()
    print("SOURCES INJECTED INTO PROMPT")
    print("-" * 70)

    if not result["sources_used"]:
        print("No sources were injected.")

        return

    for source in result["sources_used"]:
        print(
            f"{source['citation']} "
            f"{source['source']} | "
            f"chunk={source['chunk_id']} | "
            f"chunk_index={source['chunk_index']}"
        )


# ===================================================================
# DISPLAY — AUGMENTED PROMPT
# ===================================================================

def print_augmented_prompt(
    result: dict[str, Any],
) -> None:
    """
    Display the final augmented prompt.
    """

    print()
    print("AUGMENTED PROMPT")
    print("=" * 70)
    print(result["prompt"])
    print("=" * 70)


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:
    """
    Run the complete context injection demonstration.
    """

    query = (
        "When does an exporter need an export license?"
    )

    print()
    print("=" * 70)
    print("3.38 CONTEXT INJECTION & PROMPT AUGMENTATION")
    print("=" * 70)

    print()
    print("Configuration")
    print("-" * 70)

    print(
        f"Embedding model : "
        f"{EMBEDDING_MODEL}"
    )

    print(
        f"Qdrant          : "
        f"{QDRANT_URL}"
    )

    print(
        f"Collection      : "
        f"{COLLECTION_NAME}"
    )

    print(
        f"Retrieval Top-K : "
        f"{TOP_K}"
    )

    print(
        f"Max context     : "
        f"{MAX_CONTEXT_TOKENS} tokens"
    )

    print()
    print("USER QUERY")
    print("-" * 70)
    print(query)

    # ---------------------------------------------------------------
    # Stage 1 — Embed query
    # ---------------------------------------------------------------

    embedding_client = (
        create_embedding_client()
    )

    query_vector = embed_query(
        embedding_client,
        query,
    )

    print()
    print(
        f"Query embedding generated: "
        f"{len(query_vector)} dimensions"
    )

    # ---------------------------------------------------------------
    # Stage 2 — Retrieve chunks
    # ---------------------------------------------------------------

    chunks = retrieve_chunks(
        query_vector,
        k=TOP_K,
    )

    print_retrieved_chunks(
        chunks
    )

    # ---------------------------------------------------------------
    # Stage 3 + 4 — Context injection
    # ---------------------------------------------------------------

    result = build_augmented_prompt(
        query,
        chunks,
    )

    print_budget_report(
        result,
        retrieved_count=len(chunks),
    )

    # ---------------------------------------------------------------
    # Stage 5 — Sources
    # ---------------------------------------------------------------

    print_sources(
        result
    )

    # ---------------------------------------------------------------
    # Final augmented prompt
    # ---------------------------------------------------------------

    print_augmented_prompt(
        result
    )

    print()
    print("=" * 70)
    print("CONTEXT AUGMENTATION COMPLETE")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()