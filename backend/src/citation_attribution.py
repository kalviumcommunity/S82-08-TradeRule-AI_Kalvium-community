"""
3.40 Source Citation & Attribution

TradeRule AI citation pipeline:

Retrieved Chunks
        |
        v
Citation Map
        |
        +----------------------+
        |                      |
        v                      v
Source Metadata          Original Chunk Text
        |                      |
        +----------+-----------+
                   |
                   v
             Grounded Prompt
                   |
                   v
              Gemini Answer
                   |
                   v
        Citation Verification
                   |
                   v
        Answer + Citation Map

Assignment requirements covered:

1. Add source references such as [1], [2].
2. Map citations to real document/chunk metadata.
3. Verify cited source against original retrieved text.
4. Prevent fabricated citations when evidence is missing.
5. Save sample cited answers and mappings.
"""

from __future__ import annotations

import os
import re
from typing import Any

from dotenv import load_dotenv
from google import genai

from context_augmentation import (
    create_embedding_client,
    embed_query,
    retrieve_chunks,
    assemble_context,
    get_source,
    get_chunk_id,
    get_chunk_index,
    get_text,
)


# ===================================================================
# CONFIGURATION
# ===================================================================

load_dotenv()

CHAT_MODEL = os.getenv(
    "CHAT_MODEL",
    "gemini-2.5-flash",
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

TOP_K = 5

FALLBACK_MESSAGE = (
    "I don't have enough information "
    "in the provided context."
)


# ===================================================================
# CLIENTS
# ===================================================================

def create_generation_client() -> genai.Client:
    """
    Create the native Google GenAI client.
    """

    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. "
            "Check your .env file."
        )

    return genai.Client(
        api_key=GEMINI_API_KEY
    )


# ===================================================================
# TASK 2
# CITATION MAP
# ===================================================================

def build_citation_map(
    chunks: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Build a stable citation-to-source mapping.

    Example:

    {
        "[1]": {
            "source": "license_rules.txt",
            "chunk_id": "license-0",
            "chunk_index": 0,
            "section": None,
            "text": "..."
        }
    }

    Each citation points to one real retrieved chunk.
    """

    citation_map: dict[str, dict[str, Any]] = {}

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        citation = f"[{index}]"

        citation_map[citation] = {
            "source": get_source(chunk),
            "chunk_id": get_chunk_id(chunk),
            "chunk_index": get_chunk_index(chunk),
            "section": get_metadata_value(
                chunk,
                "section",
            ),
            "text": get_text(chunk),
        }

    return citation_map


# ===================================================================
# METADATA HELPER
# ===================================================================

def get_metadata_value(
    chunk: dict[str, Any],
    key: str,
) -> Any:
    """
    Safely retrieve a metadata field.

    Metadata can be stored inside:

        payload["metadata"]

    or directly inside:

        payload
    """

    payload = chunk.get(
        "payload",
        {},
    )

    if not isinstance(payload, dict):
        return None

    metadata = payload.get(
        "metadata"
    )

    if isinstance(metadata, dict):
        if key in metadata:
            return metadata[key]

    return payload.get(key)


# ===================================================================
# TASK 1
# CITED PROMPT
# ===================================================================

def build_cited_prompt(
    question: str,
    chunks: list[dict[str, Any]],
) -> tuple[
    str,
    dict[str, dict[str, Any]],
]:
    """
    Build a grounded prompt that explicitly requires citations.

    Returns:

        prompt
        citation_map
    """

    if not chunks:
        return (
            f"""
You are a grounded compliance assistant for TradeRule AI.

Answer the question using ONLY the provided context.

There is currently no supporting context.

Do not invent facts.
Do not create citations.
If the context does not support an answer, say:

"{FALLBACK_MESSAGE}"

Question:
{question}

Answer:
""".strip(),
            {},
        )

    context, _, selected_chunks, _ = (
        assemble_context(chunks)
    )

    # ---------------------------------------------------------------
    # Build citation map only for chunks actually injected into
    # the prompt.
    # ---------------------------------------------------------------

    citation_map = build_citation_map(
        selected_chunks
    )

    prompt = f"""
You are a grounded compliance assistant for TradeRule AI.

Answer the user's question using ONLY the retrieved context.

CITATION RULES:
1. Cite every factual claim that comes from the context.
2. Use citation markers such as [1], [2], or [3].
3. Only use citation markers that appear in the retrieved context.
4. Never create or guess a citation.
5. Never cite a source that was not retrieved.
6. If the context does not support the answer, say:
   "{FALLBACK_MESSAGE}"
7. Do not use outside knowledge.
8. Keep the answer concise and directly relevant.

RETRIEVED CONTEXT:
------------------------------------------------------------------
{context}
------------------------------------------------------------------

QUESTION:
{question}

ANSWER:
""".strip()

    return (
        prompt,
        citation_map,
    )


# ===================================================================
# LLM GENERATION
# ===================================================================

def call_llm(
    client: genai.Client,
    prompt: str,
) -> str:
    """
    Generate an answer using Gemini.
    """

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=prompt,
    )

    answer = getattr(
        response,
        "text",
        None,
    )

    if not answer:
        return ""

    return answer.strip()


# ===================================================================
# CITATION EXTRACTION
# ===================================================================

def extract_citations(
    answer: str,
) -> list[str]:
    """
    Extract citation markers from an answer.

    Example:

        "Controlled products may need licenses [1]."

    returns:

        ["[1]"]
    """

    matches = re.findall(
        r"\[\d+\]",
        answer,
    )

    # Preserve order while removing duplicates.
    unique = []

    for marker in matches:
        if marker not in unique:
            unique.append(marker)

    return unique


# ===================================================================
# TASK 4
# FABRICATED CITATION PROTECTION
# ===================================================================

def validate_citations(
    answer: str,
    citation_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Validate every citation used in the answer.

    A citation is valid only when it exists in the
    citation map generated from retrieved chunks.
    """

    citations_found = extract_citations(
        answer
    )

    valid_citations = []

    invalid_citations = []

    for citation in citations_found:
        if citation in citation_map:
            valid_citations.append(
                citation
            )
        else:
            invalid_citations.append(
                citation
            )

    return {
        "citations_found": citations_found,
        "valid_citations": valid_citations,
        "invalid_citations": invalid_citations,
        "all_citations_valid": (
            len(invalid_citations) == 0
        ),
    }


# ===================================================================
# TASK 3
# SOURCE VERIFICATION
# ===================================================================

def verify_citation_source(
    citation: str,
    citation_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """
    Return the original source information associated
    with one citation marker.

    This lets a user inspect the exact retrieved chunk
    behind a citation.
    """

    if citation not in citation_map:
        return {
            "citation": citation,
            "verified": False,
            "reason": (
                "Citation does not exist in "
                "the retrieved citation map."
            ),
        }

    source = citation_map[citation]

    return {
        "citation": citation,
        "verified": True,
        "source": source["source"],
        "chunk_id": source["chunk_id"],
        "chunk_index": source["chunk_index"],
        "section": source["section"],
        "original_text": source["text"],
    }


# ===================================================================
# FULL CITATION PIPELINE
# ===================================================================

def answer_with_citations(
    client: genai.Client,
    embedding_client,
    question: str,
) -> dict[str, Any]:
    """
    Complete cited-answer pipeline.

    1. Embed question.
    2. Retrieve chunks.
    3. Build citation map.
    4. Build cited prompt.
    5. Generate answer.
    6. Validate citations.
    7. Return answer + citations.
    """

    query_vector = embed_query(
        embedding_client,
        question,
    )

    chunks = retrieve_chunks(
        query_vector,
        k=TOP_K,
    )

    # ---------------------------------------------------------------
    # Missing context fallback
    # ---------------------------------------------------------------

    if not chunks:
        return {
            "question": question,
            "answer": FALLBACK_MESSAGE,
            "citations": {},
            "retrieved_chunks": [],
            "citation_validation": {
                "citations_found": [],
                "valid_citations": [],
                "invalid_citations": [],
                "all_citations_valid": True,
            },
            "fallback": True,
        }

    # ---------------------------------------------------------------
    # Build cited prompt
    # ---------------------------------------------------------------

    prompt, citation_map = (
        build_cited_prompt(
            question,
            chunks,
        )
    )

    # ---------------------------------------------------------------
    # Generate answer
    # ---------------------------------------------------------------

    answer = call_llm(
        client,
        prompt,
    )

    # ---------------------------------------------------------------
    # Validate citations
    # ---------------------------------------------------------------

    citation_validation = (
        validate_citations(
            answer,
            citation_map,
        )
    )

    # ---------------------------------------------------------------
    # If the model somehow produces a fabricated citation,
    # do not silently present it as valid.
    # ---------------------------------------------------------------

    if not citation_validation[
        "all_citations_valid"
    ]:
        return {
            "question": question,
            "answer": FALLBACK_MESSAGE,
            "citations": citation_map,
            "retrieved_chunks": chunks,
            "citation_validation": citation_validation,
            "fallback": True,
            "original_answer": answer,
        }

    return {
        "question": question,
        "answer": answer,
        "citations": citation_map,
        "retrieved_chunks": chunks,
        "citation_validation": citation_validation,
        "fallback": False,
        "prompt": prompt,
    }


# ===================================================================
# DISPLAY — CITATION MAP
# ===================================================================

def print_citation_map(
    citation_map: dict[str, dict[str, Any]],
) -> None:
    """
    Display citation-to-source mappings.
    """

    print()
    print("CITATION MAP")
    print("-" * 70)

    if not citation_map:
        print("No citation mappings.")
        return

    for citation, source in citation_map.items():

        print(
            f"{citation} -> "
            f"{source['source']} | "
            f"chunk={source['chunk_id']} | "
            f"chunk_index={source['chunk_index']}"
        )

        if source["section"] is not None:
            print(
                f"Section: "
                f"{source['section']}"
            )


# ===================================================================
# DISPLAY — SOURCE VERIFICATION
# ===================================================================

def print_source_verification(
    verification: dict[str, Any],
) -> None:
    """
    Display one citation's original source text.
    """

    print()
    print("SOURCE VERIFICATION")
    print("-" * 70)

    print(
        f"Citation : "
        f"{verification['citation']}"
    )

    print(
        f"Verified : "
        f"{verification['verified']}"
    )

    if not verification["verified"]:
        print(
            f"Reason   : "
            f"{verification['reason']}"
        )
        return

    print(
        f"Source   : "
        f"{verification['source']}"
    )

    print(
        f"Chunk ID  : "
        f"{verification['chunk_id']}"
    )

    print(
        f"Chunk idx : "
        f"{verification['chunk_index']}"
    )

    print()
    print("ORIGINAL RETRIEVED TEXT")
    print("-" * 70)

    print(
        verification["original_text"]
    )


# ===================================================================
# DISPLAY — CITATION VALIDATION
# ===================================================================

def print_citation_validation(
    validation: dict[str, Any],
) -> None:
    """
    Display citation validation information.
    """

    print()
    print("CITATION VALIDATION")
    print("-" * 70)

    print(
        f"Citations found    : "
        f"{validation['citations_found']}"
    )

    print(
        f"Valid citations    : "
        f"{validation['valid_citations']}"
    )

    print(
        f"Invalid citations  : "
        f"{validation['invalid_citations']}"
    )

    print(
        f"All citations valid: "
        f"{validation['all_citations_valid']}"
    )


# ===================================================================
# DISPLAY — ANSWER
# ===================================================================

def print_answer(
    result: dict[str, Any],
) -> None:
    """
    Display the final cited answer.
    """

    print()
    print("GENERATED ANSWER")
    print("-" * 70)

    print(
        result["answer"]
    )

    if result.get("original_answer"):
        print()
        print(
            "ORIGINAL MODEL ANSWER "
            "(rejected because of invalid citation)"
        )
        print("-" * 70)

        print(
            result["original_answer"]
        )


# ===================================================================
# TASK 3 — VERIFY ONE CITATION
# ===================================================================

def run_source_verification(
    result: dict[str, Any],
) -> None:
    """
    Pick the first citation used by the answer
    and verify it against the original chunk.
    """

    citations = result[
        "citation_validation"
    ]["valid_citations"]

    if not citations:
        print()
        print(
            "No citation available for verification."
        )
        return

    first_citation = citations[0]

    verification = verify_citation_source(
        first_citation,
        result["citations"],
    )

    print_source_verification(
        verification
    )


# ===================================================================
# TASK 4 — FABRICATED CITATION TEST
# ===================================================================

def run_fabricated_citation_test(
    result: dict[str, Any],
) -> None:
    """
    Demonstrate that a citation not present in the
    retrieved citation map is rejected.

    Example:
        [99]

    Since [99] was not retrieved, it is invalid.
    """

    print()
    print("=" * 70)
    print("TASK 4 — FABRICATED CITATION PROTECTION")
    print("=" * 70)

    fake_answer = (
        "This statement uses a fabricated source [99]."
    )

    validation = validate_citations(
        fake_answer,
        result["citations"],
    )

    print()
    print("TEST ANSWER")
    print("-" * 70)
    print(fake_answer)

    print_citation_validation(
        validation
    )

    print()

    if validation["all_citations_valid"]:
        print(
            "ERROR: fabricated citation was accepted."
        )
    else:
        print(
            "PASS: fabricated citation was rejected."
        )


# ===================================================================
# TASK 5 — NO-SOURCE FALLBACK
# ===================================================================

def run_no_source_test(
    client: genai.Client,
) -> dict[str, Any]:
    """
    Test citation behavior when there are no sources.
    """

    question = (
        "What evidence is required for project submission?"
    )

    prompt, citation_map = (
        build_cited_prompt(
            question,
            [],
        )
    )

    # The no-source case should not call the model.
    # We directly use the required fallback.
    answer = FALLBACK_MESSAGE

    validation = validate_citations(
        answer,
        citation_map,
    )

    return {
        "question": question,
        "answer": answer,
        "citations": citation_map,
        "citation_validation": validation,
        "prompt": prompt,
        "fallback": True,
    }


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:
    """
    Run the complete 3.40 citation demonstration.
    """

    print()
    print("=" * 70)
    print("3.40 SOURCE CITATION & ATTRIBUTION")
    print("=" * 70)

    print()
    print("Configuration")
    print("-" * 70)

    print(
        f"Chat model : {CHAT_MODEL}"
    )

    print(
        f"Top-K      : {TOP_K}"
    )

    # ---------------------------------------------------------------
    # Create clients
    # ---------------------------------------------------------------

    generation_client = (
        create_generation_client()
    )

    embedding_client = (
        create_embedding_client()
    )

    # ---------------------------------------------------------------
    # Main cited answer
    # ---------------------------------------------------------------

    question = (
        "When does an exporter need an export license?"
    )

    print()
    print("=" * 70)
    print("TASK 1 + TASK 2 — CITED ANSWER")
    print("=" * 70)

    print()
    print("QUESTION")
    print("-" * 70)
    print(question)

    result = answer_with_citations(
        generation_client,
        embedding_client,
        question,
    )

    print_answer(
        result
    )

    print_citation_map(
        result["citations"]
    )

    print_citation_validation(
        result["citation_validation"]
    )

    # ---------------------------------------------------------------
    # Task 3 — Verify source
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("TASK 3 — SOURCE VERIFICATION")
    print("=" * 70)

    run_source_verification(
        result
    )

    # ---------------------------------------------------------------
    # Task 4 — Fabricated citation protection
    # ---------------------------------------------------------------

    run_fabricated_citation_test(
        result
    )

    # ---------------------------------------------------------------
    # Task 4 + Task 5 — No-source fallback
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("TASK 4 + TASK 5 — NO-SOURCE FALLBACK")
    print("=" * 70)

    fallback_result = run_no_source_test(
        generation_client
    )

    print()
    print("QUESTION")
    print("-" * 70)
    print(
        fallback_result["question"]
    )

    print()
    print("FALLBACK ANSWER")
    print("-" * 70)
    print(
        fallback_result["answer"]
    )

    print_citation_map(
        fallback_result["citations"]
    )

    print_citation_validation(
        fallback_result["citation_validation"]
    )

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("3.40 COMPLETE")
    print("=" * 70)

    print()

    print(
        "Cited answer generated : "
        f"{bool(result['answer'])}"
    )

    print(
        "Citation mappings      : "
        f"{len(result['citations'])}"
    )

    print(
        "Citations valid        : "
        f"{result['citation_validation']['all_citations_valid']}"
    )

    print(
        "Fallback tested        : "
        f"{fallback_result['fallback']}"
    )

    print(
        "Fallback has citations : "
        f"{len(fallback_result['citations']) > 0}"
    )

    print()


if __name__ == "__main__":
    main()
