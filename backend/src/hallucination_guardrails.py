"""
3.41 Hallucination Guardrails & Refusal Handling

TradeRule AI guardrail flow:

User Question
      |
      v
Query Embedding
      |
      v
Qdrant Retrieval
      |
      v
Retrieval Quality Check
      |
      +-----------------------------+
      |                             |
      v                             v
Strong Context                 Weak / Empty Context
      |                             |
      v                             v
Citation Pipeline              SAFE REFUSAL
      |                         No LLM Call
      v
Grounded Gemini Answer
      |
      v
Citation Validation
      |
      +-----------------------------+
      |                             |
      v                             v
Valid Citations              Invalid Citation
      |                             |
      v                             v
Answer + Sources              SAFE REFUSAL
"""


from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


# ===================================================================
# EXISTING TRADE RULE AI PIPELINE
# ===================================================================

from context_augmentation import (
    create_embedding_client,
    embed_query,
    retrieve_chunks,
)

from citation_attribution import (
    build_cited_prompt,
    call_llm,
    create_generation_client,
    validate_citations,
)


# ===================================================================
# CONFIGURATION
# ===================================================================

load_dotenv()


TOP_K = 5

# Minimum similarity score required for a retrieved chunk
# to be considered supporting evidence.
MIN_TOP_SCORE = 0.72

# At least this many chunks must pass the threshold.
MIN_SUPPORTING_CHUNKS = 1

# Safe response when evidence is insufficient.
REFUSAL_MESSAGE = (
    "I don't have enough reliable context to answer that."
)


# ===================================================================
# RESULT MODEL
# ===================================================================

@dataclass
class GuardrailResult:
    """
    Result returned by the hallucination guardrail.
    """

    status: str
    answer: str
    sources: list[dict[str, Any]]

    retrieval_count: int
    top_score: float
    supporting_chunks: int
    threshold: float

    reason: str


# ===================================================================
# RETRIEVAL QUALITY CHECK
# ===================================================================

def retrieval_is_strong(
    chunks: list[dict[str, Any]],
    min_top_score: float = MIN_TOP_SCORE,
    min_supporting_chunks: int = MIN_SUPPORTING_CHUNKS,
) -> bool:
    """
    Determine whether retrieved context is strong enough
    to allow answer generation.

    Retrieval is accepted only when:
      1. At least one chunk exists.
      2. Enough chunks meet the similarity threshold.
    """

    if not chunks:
        return False

    supporting_chunks = sum(
        1
        for chunk in chunks
        if float(chunk.get("score", 0.0)) >= min_top_score
    )

    return supporting_chunks >= min_supporting_chunks


def evaluate_retrieval(
    chunks: list[dict[str, Any]],
    min_top_score: float = MIN_TOP_SCORE,
    min_supporting_chunks: int = MIN_SUPPORTING_CHUNKS,
) -> dict[str, Any]:
    """
    Calculate deterministic retrieval-quality metrics.
    """

    scores = [
        float(chunk.get("score", 0.0))
        for chunk in chunks
    ]

    top_score = max(scores) if scores else 0.0

    supporting_chunks = sum(
        1
        for score in scores
        if score >= min_top_score
    )

    accepted = (
        bool(chunks)
        and supporting_chunks >= min_supporting_chunks
    )

    return {
        "strong": accepted,
        "top_score": top_score,
        "supporting_chunks": supporting_chunks,
        "retrieval_count": len(chunks),
        "threshold": min_top_score,
        "minimum_supporting_chunks": min_supporting_chunks,
    }


# ===================================================================
# GUARDED ANSWER PIPELINE
# ===================================================================

def guarded_answer(
    question: str,
    embedding_client: Any,
    generation_client: Any,
    k: int = TOP_K,
    min_top_score: float = MIN_TOP_SCORE,
    min_supporting_chunks: int = MIN_SUPPORTING_CHUNKS,
) -> GuardrailResult:
    """
    Execute the real TradeRule AI retrieval pipeline
    with hallucination protection.

    Important:
    The LLM is NEVER called when retrieval is weak.
    """

    # ---------------------------------------------------------------
    # STEP 1 — EMBED USER QUESTION
    # ---------------------------------------------------------------

    query_vector = embed_query(
        embedding_client,
        question,
    )

    # ---------------------------------------------------------------
    # STEP 2 — RETRIEVE RELEVANT CHUNKS
    # ---------------------------------------------------------------

    chunks = retrieve_chunks(
        query_vector,
        k=k,
    )

    # ---------------------------------------------------------------
    # STEP 3 — CHECK RETRIEVAL QUALITY
    # ---------------------------------------------------------------

    quality = evaluate_retrieval(
        chunks,
        min_top_score=min_top_score,
        min_supporting_chunks=min_supporting_chunks,
    )

    # ---------------------------------------------------------------
    # STEP 4 — SAFE REFUSAL
    # ---------------------------------------------------------------

    # This happens BEFORE the LLM is called.
    if not quality["strong"]:

        return GuardrailResult(
            status="refused_weak_context",
            answer=REFUSAL_MESSAGE,
            sources=[],

            retrieval_count=quality["retrieval_count"],
            top_score=quality["top_score"],
            supporting_chunks=quality["supporting_chunks"],
            threshold=quality["threshold"],

            reason=(
                "Retrieval context did not meet the "
                "minimum relevance requirement."
            ),
        )

    # ---------------------------------------------------------------
    # STEP 5 — BUILD EXISTING 3.40 CITATION PROMPT
    # ---------------------------------------------------------------

    prompt, citation_map = build_cited_prompt(
        question,
        chunks,
    )

    # ---------------------------------------------------------------
    # STEP 6 — GENERATE ANSWER
    # ---------------------------------------------------------------

    answer = call_llm(
        generation_client,
        prompt,
    )

    # ---------------------------------------------------------------
    # STEP 7 — VALIDATE GENERATED CITATIONS
    # ---------------------------------------------------------------

    citation_validation = validate_citations(
        answer,
        citation_map,
    )

    # ---------------------------------------------------------------
    # STEP 8 — PROTECT AGAINST FABRICATED CITATIONS
    # ---------------------------------------------------------------

    if not citation_validation["all_citations_valid"]:

        return GuardrailResult(
            status="refused_invalid_citation",
            answer=REFUSAL_MESSAGE,
            sources=[],

            retrieval_count=quality["retrieval_count"],
            top_score=quality["top_score"],
            supporting_chunks=quality["supporting_chunks"],
            threshold=quality["threshold"],

            reason=(
                "Generated answer contained a citation "
                "that could not be verified against "
                "retrieved sources."
            ),
        )

    # ---------------------------------------------------------------
    # STEP 9 — BUILD SOURCE LIST
    # ---------------------------------------------------------------

    sources: list[dict[str, Any]] = []

    for citation, source_data in citation_map.items():

        sources.append(
            {
                "citation": citation,
                "source": source_data.get("source"),
                "chunk_id": source_data.get("chunk_id"),
                "chunk_index": source_data.get("chunk_index"),
                "section": source_data.get("section"),
            }
        )

    # ---------------------------------------------------------------
    # STEP 10 — RETURN CONFIDENT GROUNDED ANSWER
    # ---------------------------------------------------------------

    return GuardrailResult(
        status="answered",
        answer=answer,
        sources=sources,

        retrieval_count=quality["retrieval_count"],
        top_score=quality["top_score"],
        supporting_chunks=quality["supporting_chunks"],
        threshold=quality["threshold"],

        reason=(
            "Retrieval context passed the relevance "
            "guardrail and citations were validated."
        ),
    )


# ===================================================================
# UNIT TESTS — GUARDRAIL DECISION LOGIC
# ===================================================================

def run_guardrail_tests() -> None:
    """
    Deterministic tests for:
      - strong context
      - weak context
      - empty context
      - threshold enforcement
      - safe refusal
    """

    # ---------------------------------------------------------------
    # STRONG RETRIEVAL
    # ---------------------------------------------------------------

    strong_chunks = [
        {
            "score": 0.794573,
            "source": "license_rules.txt",
            "chunk_id": "license-0",
            "text": (
                "Certain controlled products may require "
                "an export license before shipment depending "
                "on destination and classification."
            ),
        },
        {
            "score": 0.761561,
            "source": "export_guidelines.md",
            "chunk_id": "export-0",
            "text": (
                "Exporters should verify export control "
                "requirements, destination restrictions, "
                "required licenses, and customs documentation."
            ),
        },
    ]

    # ---------------------------------------------------------------
    # WEAK RETRIEVAL
    # ---------------------------------------------------------------

    weak_chunks = [
        {
            "score": 0.421000,
            "source": "import_rules.html",
            "chunk_id": "import-0",
            "text": "Import requirements and documentation.",
        },
        {
            "score": 0.388000,
            "source": "customs_requirements.txt",
            "chunk_id": "customs-0",
            "text": "Customs documentation requirements.",
        },
    ]

    # ---------------------------------------------------------------
    # EMPTY RETRIEVAL
    # ---------------------------------------------------------------

    empty_chunks: list[dict[str, Any]] = []

    # ---------------------------------------------------------------
    # STRONG CASE
    # ---------------------------------------------------------------

    strong_quality = evaluate_retrieval(
        strong_chunks
    )

    print("\nTASK 1 + TASK 3 — RETRIEVAL QUALITY CHECK")
    print("-" * 70)

    print("Strong-context case:")
    print(
        f"  Retrieval count       : "
        f"{strong_quality['retrieval_count']}"
    )
    print(
        f"  Top score             : "
        f"{strong_quality['top_score']:.6f}"
    )
    print(
        f"  Supporting chunks     : "
        f"{strong_quality['supporting_chunks']}"
    )
    print(
        f"  Threshold             : "
        f"{strong_quality['threshold']}"
    )
    print(
        f"  Retrieval accepted    : "
        f"{strong_quality['strong']}"
    )

    # ---------------------------------------------------------------
    # WEAK CASE
    # ---------------------------------------------------------------

    weak_quality = evaluate_retrieval(
        weak_chunks
    )

    print("\nWeak-context case:")
    print(
        f"  Retrieval count       : "
        f"{weak_quality['retrieval_count']}"
    )
    print(
        f"  Top score             : "
        f"{weak_quality['top_score']:.6f}"
    )
    print(
        f"  Supporting chunks     : "
        f"{weak_quality['supporting_chunks']}"
    )
    print(
        f"  Threshold             : "
        f"{weak_quality['threshold']}"
    )
    print(
        f"  Retrieval accepted    : "
        f"{weak_quality['strong']}"
    )

    # ---------------------------------------------------------------
    # EMPTY CASE
    # ---------------------------------------------------------------

    empty_quality = evaluate_retrieval(
        empty_chunks
    )

    print("\nEmpty-context case:")
    print(
        f"  Retrieval count       : "
        f"{empty_quality['retrieval_count']}"
    )
    print(
        f"  Top score             : "
        f"{empty_quality['top_score']:.6f}"
    )
    print(
        f"  Supporting chunks     : "
        f"{empty_quality['supporting_chunks']}"
    )
    print(
        f"  Retrieval accepted    : "
        f"{empty_quality['strong']}"
    )

    # ---------------------------------------------------------------
    # SAFE REFUSAL
    # ---------------------------------------------------------------

    weak_refusal_correct = (
        not weak_quality["strong"]
        and REFUSAL_MESSAGE
        == "I don't have enough reliable context to answer that."
    )

    empty_refusal_correct = (
        not empty_quality["strong"]
    )

    print("\nTASK 2 — SAFE REFUSAL")
    print("-" * 70)

    print(
        f"Weak context refused     : "
        f"{not weak_quality['strong']}"
    )

    print(
        f"Empty context refused    : "
        f"{not empty_quality['strong']}"
    )

    print(
        f"Refusal message valid    : "
        f"{weak_refusal_correct}"
    )

    print(
        f"Empty refusal valid      : "
        f"{empty_refusal_correct}"
    )

    # ---------------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------------

    checks = [
        strong_quality["strong"],
        not weak_quality["strong"],
        not empty_quality["strong"],
        weak_refusal_correct,
        empty_refusal_correct,
    ]

    print("\nGUARDRAIL UNIT TESTS")
    print("-" * 70)

    print(
        f"Strong context accepted : "
        f"{strong_quality['strong']}"
    )

    print(
        f"Weak context rejected   : "
        f"{not weak_quality['strong']}"
    )

    print(
        f"Empty context rejected  : "
        f"{not empty_quality['strong']}"
    )

    print(
        f"Safe refusal valid      : "
        f"{weak_refusal_correct}"
    )

    print(
        f"ALL UNIT CHECKS PASS    : "
        f"{all(checks)}"
    )


# ===================================================================
# REAL PIPELINE DEMO
# ===================================================================

def run_real_pipeline_demo() -> None:
    """
    Run real Qdrant retrieval against:
      1. a known supported TradeRule question
      2. an unsupported question

    The unsupported case must be refused before
    Gemini generation.
    """

    print("\n")
    print("=" * 70)
    print("3.41 REAL PIPELINE — HALLUCINATION GUARDRAIL")
    print("=" * 70)

    # ---------------------------------------------------------------
    # CREATE CLIENTS
    # ---------------------------------------------------------------

    embedding_client = create_embedding_client()
    generation_client = create_generation_client()

    # ---------------------------------------------------------------
    # CASE 1 — STRONG / SUPPORTED
    # ---------------------------------------------------------------

    strong_question = (
        "When does an exporter need an export license?"
    )

    print("\nCASE 1 — STRONG CONTEXT")
    print("-" * 70)

    print(
        f"Question: {strong_question}"
    )

    strong_result = guarded_answer(
        question=strong_question,
        embedding_client=embedding_client,
        generation_client=generation_client,
    )

    print(
        f"Status: {strong_result.status}"
    )

    print(
        f"Retrieval count: "
        f"{strong_result.retrieval_count}"
    )

    print(
        f"Top score: "
        f"{strong_result.top_score:.6f}"
    )

    print(
        f"Supporting chunks: "
        f"{strong_result.supporting_chunks}"
    )

    print(
        f"Threshold: "
        f"{strong_result.threshold}"
    )

    print(
        f"Answer: "
        f"{strong_result.answer}"
    )

    print(
        f"Sources: "
        f"{strong_result.sources}"
    )

    print(
        f"Reason: "
        f"{strong_result.reason}"
    )

    # ---------------------------------------------------------------
    # CASE 2 — WEAK / UNSUPPORTED
    # ---------------------------------------------------------------

    weak_question = (
        "What evidence is required for project submission?"
    )

    print("\nCASE 2 — WEAK / UNSUPPORTED CONTEXT")
    print("-" * 70)

    print(
        f"Question: {weak_question}"
    )

    weak_result = guarded_answer(
        question=weak_question,
        embedding_client=embedding_client,
        generation_client=generation_client,
    )

    print(
        f"Status: {weak_result.status}"
    )

    print(
        f"Retrieval count: "
        f"{weak_result.retrieval_count}"
    )

    print(
        f"Top score: "
        f"{weak_result.top_score:.6f}"
    )

    print(
        f"Supporting chunks: "
        f"{weak_result.supporting_chunks}"
    )

    print(
        f"Threshold: "
        f"{weak_result.threshold}"
    )

    print(
        f"Answer: "
        f"{weak_result.answer}"
    )

    print(
        f"Sources: "
        f"{weak_result.sources}"
    )

    print(
        f"Reason: "
        f"{weak_result.reason}"
    )

    # ---------------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------------

    strong_answered = (
        strong_result.status == "answered"
    )

    strong_has_answer = bool(
        strong_result.answer
    )

    strong_has_sources = bool(
        strong_result.sources
    )

    weak_refused = (
        weak_result.status
        == "refused_weak_context"
    )

    weak_safe_message = (
        weak_result.answer
        == REFUSAL_MESSAGE
    )

    weak_has_no_sources = (
        not weak_result.sources
    )

    print("\nVALIDATION CHECKS")
    print("-" * 70)

    print(
        f"strong_answered            : "
        f"{strong_answered}"
    )

    print(
        f"strong_has_answer          : "
        f"{strong_has_answer}"
    )

    print(
        f"strong_has_sources         : "
        f"{strong_has_sources}"
    )

    print(
        f"weak_refused               : "
        f"{weak_refused}"
    )

    print(
        f"weak_safe_message          : "
        f"{weak_safe_message}"
    )

    print(
        f"weak_has_no_sources        : "
        f"{weak_has_no_sources}"
    )

    real_checks = [
        strong_answered,
        strong_has_answer,
        strong_has_sources,
        weak_refused,
        weak_safe_message,
        weak_has_no_sources,
    ]

    print(
        f"\nALL REAL PIPELINE CHECKS PASS: "
        f"{all(real_checks)}"
    )


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:

    print("=" * 70)
    print("3.41 HALLUCINATION GUARDRAILS & REFUSAL HANDLING")
    print("=" * 70)

    print("\nCONFIGURATION")
    print("-" * 70)

    print(
        f"Minimum top score        : "
        f"{MIN_TOP_SCORE}"
    )

    print(
        f"Minimum supporting chunks: "
        f"{MIN_SUPPORTING_CHUNKS}"
    )

    print(
        f"Top-K retrieval           : "
        f"{TOP_K}"
    )

    print(
        f"Refusal message           : "
        f"{REFUSAL_MESSAGE}"
    )

    # Deterministic guardrail tests.
    run_guardrail_tests()

    # Actual Qdrant + Gemini pipeline.
    run_real_pipeline_demo()

    print("\n")
    print("=" * 70)
    print("3.41 COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()