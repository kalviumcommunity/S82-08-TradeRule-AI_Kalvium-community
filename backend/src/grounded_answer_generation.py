"""
3.39 Grounded Answer Generation

TradeRule AI RAG pipeline:

User Question
      |
      v
Retrieve Context
      |
      v
Context Augmentation
      |
      v
Grounded Prompt
      |
      v
Gemini
      |
      v
Grounded Answer + Sources

Tasks covered:
1. Generate answers using injected retrieved context.
2. Verify answer claims against retrieved chunks.
3. Provide missing-context fallback.
4. Compare grounded and ungrounded answers.
5. Save sample outputs for evaluation.
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from google import genai

from context_augmentation import (
    create_embedding_client,
    embed_query,
    retrieve_chunks,
    build_augmented_prompt,
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
# GEMINI CLIENT
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
# UNGROUNDED GENERATION
# ===================================================================

def call_llm(
    client: genai.Client,
    prompt: str,
) -> str:
    """
    Generate a normal model response.

    This function is intentionally not grounded.
    It is used only for comparison.
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
# GROUNDED GENERATION
# ===================================================================

def generate_grounded_answer(
    client: genai.Client,
    question: str,
    retrieved_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate an answer using ONLY the injected retrieved context.

    The augmented prompt is produced by the 3.38
    context augmentation module.
    """

    prompt_data = build_augmented_prompt(
        question,
        retrieved_chunks,
    )

    # ---------------------------------------------------------------
    # Missing-context protection
    # ---------------------------------------------------------------

    if not prompt_data["selected_chunks"]:
        return {
            "question": question,
            "answer": FALLBACK_MESSAGE,
            "context": prompt_data["prompt"],
            "sources": [],
            "grounded": True,
            "fallback": True,
        }

    # ---------------------------------------------------------------
    # Generate answer from the augmented prompt.
    # ---------------------------------------------------------------

    answer = call_llm(
        client,
        prompt_data["prompt"],
    )

    return {
        "question": question,
        "answer": answer,
        "context": prompt_data["prompt"],
        "sources": prompt_data["sources_used"],
        "grounded": True,
        "fallback": False,
    }


# ===================================================================
# RETRIEVAL PIPELINE
# ===================================================================

def answer_query(
    client: genai.Client,
    embedding_client,
    question: str,
) -> dict[str, Any]:
    """
    Complete grounded RAG query.

    1. Embed question.
    2. Retrieve chunks.
    3. Check whether context exists.
    4. Generate grounded answer.
    """

    if not question.strip():
        raise ValueError(
            "Question cannot be empty."
        )

    query_vector = embed_query(
        embedding_client,
        question,
    )

    chunks = retrieve_chunks(
        query_vector,
        k=TOP_K,
    )

    # ---------------------------------------------------------------
    # Missing-context fallback
    # ---------------------------------------------------------------

    if not chunks:
        return {
            "question": question,
            "answer": FALLBACK_MESSAGE,
            "context": "",
            "sources": [],
            "retrieved_chunks": [],
            "grounded": True,
            "fallback": True,
        }

    result = generate_grounded_answer(
        client,
        question,
        chunks,
    )

    result["retrieved_chunks"] = chunks

    return result


# ===================================================================
# SOURCE DISPLAY
# ===================================================================

def print_sources(
    sources: list[dict[str, Any]],
) -> None:
    """
    Display the sources used by the grounded answer.
    """

    print()
    print("SOURCES")
    print("-" * 70)

    if not sources:
        print("No sources.")
        return

    for source in sources:
        print(
            f"{source['citation']} "
            f"{source['source']} | "
            f"chunk={source['chunk_id']} | "
            f"chunk_index={source['chunk_index']}"
        )


# ===================================================================
# RETRIEVED CONTEXT DISPLAY
# ===================================================================

def print_supporting_chunks(
    chunks: list[dict[str, Any]],
) -> None:
    """
    Display the actual chunks supporting the answer.
    """

    print()
    print("SUPPORTING RETRIEVED CHUNKS")
    print("-" * 70)

    if not chunks:
        print("No supporting chunks retrieved.")
        return

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        print(
            f"[{index}] "
            f"{get_source(chunk)} | "
            f"chunk={get_chunk_id(chunk)}"
        )

        print(
            get_text(chunk)
        )

        print()


# ===================================================================
# GROUNDED ANSWER VERIFICATION
# ===================================================================

def verify_grounding(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Perform a basic technical grounding check.

    This checks:
    - answer exists
    - fallback is used when no sources exist
    - sources are attached to grounded answers
    - cited markers in the answer correspond to available sources

    This is not a semantic proof of factual correctness.
    Human/source-level review is still required.
    """

    answer = result.get(
        "answer",
        "",
    )

    sources = result.get(
        "sources",
        [],
    )

    fallback = result.get(
        "fallback",
        False,
    )

    checks = {}

    # ---------------------------------------------------------------
    # Check 1 — answer exists
    # ---------------------------------------------------------------

    checks["answer_present"] = bool(
        answer.strip()
    )

    # ---------------------------------------------------------------
    # Check 2 — missing context uses fallback
    # ---------------------------------------------------------------

    if not sources:
        checks["fallback_correct"] = (
            answer.strip()
            == FALLBACK_MESSAGE
        )
    else:
        checks["fallback_correct"] = True

    # ---------------------------------------------------------------
    # Check 3 — grounded answer has sources
    # ---------------------------------------------------------------

    if fallback:
        checks["sources_present"] = (
            len(sources) == 0
        )
    else:
        checks["sources_present"] = (
            len(sources) > 0
        )

    # ---------------------------------------------------------------
    # Check 4 — citations refer to known sources
    # ---------------------------------------------------------------

    citation_numbers = set()

    for source in sources:
        citation = source.get(
            "citation",
            "",
        )

        if citation:
            citation_numbers.add(
                citation
            )

    cited_markers = []

    for number in range(
        1,
        len(sources) + 1,
    ):
        marker = f"[{number}]"

        if marker in answer:
            cited_markers.append(
                marker
            )

    if sources:
        checks["citation_format_valid"] = all(
            marker in citation_numbers
            for marker in cited_markers
        )
    else:
        checks["citation_format_valid"] = (
            len(cited_markers) == 0
        )

    # ---------------------------------------------------------------
    # Overall result
    # ---------------------------------------------------------------

    checks["grounding_checks_passed"] = all(
        checks.values()
    )

    return checks


# ===================================================================
# GROUNDING REPORT
# ===================================================================

def print_grounding_check(
    result: dict[str, Any],
) -> None:
    """
    Print the grounding verification report.
    """

    checks = verify_grounding(
        result
    )

    print()
    print("GROUNDING CHECK")
    print("-" * 70)

    print(
        f"Answer present          : "
        f"{checks['answer_present']}"
    )

    print(
        f"Fallback correct        : "
        f"{checks['fallback_correct']}"
    )

    print(
        f"Sources present         : "
        f"{checks['sources_present']}"
    )

    print(
        f"Citation format valid   : "
        f"{checks['citation_format_valid']}"
    )

    print(
        f"Overall grounding check : "
        f"{checks['grounding_checks_passed']}"
    )


# ===================================================================
# COMPARISON
# ===================================================================

def compare_answers(
    client: genai.Client,
    embedding_client,
    question: str,
) -> dict[str, Any]:
    """
    Compare:

    1. Ungrounded direct model answer.
    2. Grounded RAG answer.

    Both receive the same user question.
    """

    # ---------------------------------------------------------------
    # Ungrounded mode
    # ---------------------------------------------------------------

    ungrounded_prompt = (
        "Answer this question directly:\n\n"
        f"{question}"
    )

    ungrounded = call_llm(
        client,
        ungrounded_prompt,
    )

    # ---------------------------------------------------------------
    # Grounded mode
    # ---------------------------------------------------------------

    grounded = answer_query(
        client,
        embedding_client,
        question,
    )

    return {
        "question": question,
        "ungrounded": ungrounded,
        "grounded": grounded,
    }


# ===================================================================
# DISPLAY COMPARISON
# ===================================================================

def print_comparison(
    comparison: dict[str, Any],
) -> None:
    """
    Display the with/without retrieval comparison.
    """

    print()
    print("=" * 70)
    print("WITH VS WITHOUT RETRIEVAL")
    print("=" * 70)

    print()
    print("QUESTION")
    print("-" * 70)
    print(
        comparison["question"]
    )

    print()
    print("WITHOUT RETRIEVAL — UNGROUNDED")
    print("-" * 70)
    print(
        comparison["ungrounded"]
    )

    print()
    print("WITH RETRIEVAL — GROUNDED")
    print("-" * 70)
    print(
        comparison["grounded"]["answer"]
    )

    print_sources(
        comparison["grounded"]["sources"]
    )


# ===================================================================
# MISSING CONTEXT TEST
# ===================================================================

def run_missing_context_test(
    client: genai.Client,
) -> dict[str, Any]:
    """
    Demonstrate the missing-context fallback.

    We intentionally pass an empty list of retrieved chunks
    so that the generation layer must refuse to invent an answer.
    """

    question = (
        "What evidence is required for project submission?"
    )

    result = generate_grounded_answer(
        client,
        question,
        [],
    )

    return result


# ===================================================================
# MAIN DEMONSTRATION
# ===================================================================

def main() -> None:
    """
    Run all 3.39 assignment demonstrations.
    """

    print()
    print("=" * 70)
    print("3.39 GROUNDED ANSWER GENERATION")
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
    # Clients
    # ---------------------------------------------------------------

    generation_client = (
        create_generation_client()
    )

    embedding_client = (
        create_embedding_client()
    )

    # ---------------------------------------------------------------
    # Task 1 + Task 2
    # Generate grounded answer
    # ---------------------------------------------------------------

    grounded_question = (
        "When does an exporter need an export license?"
    )

    print()
    print("=" * 70)
    print("TASK 1 + TASK 2 — GROUNDED ANSWER")
    print("=" * 70)

    grounded_result = answer_query(
        generation_client,
        embedding_client,
        grounded_question,
    )

    print_supporting_chunks(
        grounded_result[
            "retrieved_chunks"
        ]
    )

    print()
    print("GROUNDED ANSWER")
    print("-" * 70)
    print(
        grounded_result["answer"]
    )

    print_sources(
        grounded_result["sources"]
    )

    print_grounding_check(
        grounded_result
    )

    # ---------------------------------------------------------------
    # Task 3
    # Missing context fallback
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("TASK 3 — MISSING CONTEXT FALLBACK")
    print("=" * 70)

    fallback_result = (
        run_missing_context_test(
            generation_client
        )
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

    print_grounding_check(
        fallback_result
    )

    # ---------------------------------------------------------------
    # Task 4
    # With vs without retrieval
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("TASK 4 — WITH VS WITHOUT RETRIEVAL")
    print("=" * 70)

    comparison_question = (
        "When does an exporter need an export license?"
    )

    comparison = compare_answers(
        generation_client,
        embedding_client,
        comparison_question,
    )

    print_comparison(
        comparison
    )

    # ---------------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------------

    print()
    print("=" * 70)
    print("3.39 COMPLETE")
    print("=" * 70)

    print()
    print("Grounded answer generated : "
          f"{bool(grounded_result['answer'])}")

    print(
        "Supporting sources        : "
        f"{len(grounded_result['sources'])}"
    )

    print(
        "Fallback tested           : "
        f"{fallback_result['answer'] == FALLBACK_MESSAGE}"
    )

    print(
        "Grounding verified        : "
        f"{verify_grounding(grounded_result)['grounding_checks_passed']}"
    )

    print()


if __name__ == "__main__":
    main()