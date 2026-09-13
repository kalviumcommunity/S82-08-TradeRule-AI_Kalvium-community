"""
3.42 Conversational RAG & Follow-Up Context

TradeRule AI conversational RAG flow:

Conversation History
        |
        v
Latest Follow-Up Question
        |
        v
Standalone Query Rewriting
        |
        v
Embedding
        |
        v
Qdrant Retrieval
        |
        v
3.41 Retrieval Guardrail
        |
        +---------------------------+
        |                           |
        v                           v
Strong Context              Weak Context
        |                           |
        v                           v
3.40 Citation Pipeline        Safe Refusal
        |
        v
Grounded Answer + Sources
        |
        v
Append Turn to History
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

from context_augmentation import (
    create_embedding_client,
    embed_query,
    retrieve_chunks,
    count_tokens,
)

from citation_attribution import (
    build_cited_prompt,
    call_llm,
    create_generation_client,
    validate_citations,
)

from hallucination_guardrails import (
    evaluate_retrieval,
    MIN_TOP_SCORE,
    MIN_SUPPORTING_CHUNKS,
    REFUSAL_MESSAGE,
)


# ===================================================================
# CONFIGURATION
# ===================================================================

load_dotenv()

TOP_K = 5

# Keep the conversation context deliberately short.
MAX_HISTORY_TOKENS = 1200

CHAT_MODEL = os.getenv(
    "CHAT_MODEL",
    "gemini-2.5-flash",
)


# ===================================================================
# DATA MODEL
# ===================================================================

@dataclass
class ConversationTurn:
    """
    One user/assistant conversation turn.
    """

    user: str
    assistant: str


# ===================================================================
# CONVERSATION HISTORY
# ===================================================================

class ConversationHistory:
    """
    Rolling conversation history.

    The history is used for query rewriting only.
    Retrieved source chunks remain the grounding source
    for the final answer.
    """

    def __init__(
        self,
        max_tokens: int = MAX_HISTORY_TOKENS,
    ) -> None:

        self.max_tokens = max_tokens

        self.turns: list[ConversationTurn] = []

    def add_turn(
        self,
        user: str,
        assistant: str,
    ) -> None:
        """
        Add a completed user/assistant turn.
        """

        self.turns.append(
            ConversationTurn(
                user=user,
                assistant=assistant,
            )
        )

        self._trim_to_budget()

    def _render_turn(
        self,
        turn: ConversationTurn,
    ) -> str:
        """
        Render one turn for the rewrite prompt.
        """

        return (
            f"User: {turn.user}\n"
            f"Assistant: {turn.assistant}"
        )

    def as_text(self) -> str:
        """
        Return history as text.
        """

        if not self.turns:
            return "(No previous conversation.)"

        return "\n\n".join(
            self._render_turn(turn)
            for turn in self.turns
        )

    def token_count(self) -> int:
        """
        Count the current history tokens.
        """

        return count_tokens(
            self.as_text()
        )

    def _trim_to_budget(self) -> None:
        """
        Remove oldest turns until the rolling history
        fits inside the configured token budget.
        """

        while (
            len(self.turns) > 1
            and self.token_count() > self.max_tokens
        ):
            self.turns.pop(0)

    def __len__(self) -> int:
        return len(self.turns)


# ===================================================================
# FOLLOW-UP QUERY REWRITING
# ===================================================================

def build_rewrite_prompt(
    history: ConversationHistory,
    question: str,
) -> str:
    """
    Build a prompt that converts a follow-up question into
    a standalone retrieval query.

    The model is explicitly instructed NOT to answer the question.
    """

    return f"""
You rewrite follow-up questions for a retrieval system.

Your task:
Rewrite the user's latest question as ONE standalone search query.

Rules:
1. Use conversation history only to resolve references such as:
   "it", "that", "the deadline", "what about the video", etc.
2. Preserve the user's original intent.
3. Include the important subject from earlier turns when needed.
4. Do not answer the question.
5. Do not add facts that are not present in the conversation.
6. Return only the standalone search query.
7. Do not add quotation marks.
8. Do not add explanations.

Conversation history:
{history.as_text()}

Latest user question:
{question}

Standalone retrieval query:
""".strip()


def rewrite_followup(
    client: Any,
    history: ConversationHistory,
    question: str,
) -> str:
    """
    Rewrite a follow-up into a standalone query.
    """

    prompt = build_rewrite_prompt(
        history,
        question,
    )

    rewritten = call_llm(
        client,
        prompt,
    ).strip()

    # Defensive cleanup if the model returns surrounding quotes.
    rewritten = rewritten.strip("\"'")

    if not rewritten:
        return question

    return rewritten


# ===================================================================
# RETRIEVAL USING REWRITTEN QUERY
# ===================================================================

def retrieve_for_followup(
    embedding_client: Any,
    standalone_query: str,
    k: int = TOP_K,
) -> list[dict[str, Any]]:
    """
    Embed the rewritten standalone query and retrieve
    relevant chunks from Qdrant.
    """

    query_vector = embed_query(
        embedding_client,
        standalone_query,
    )

    chunks = retrieve_chunks(
        query_vector,
        k=k,
    )

    return chunks


# ===================================================================
# GROUNDED ANSWER USING RETRIEVED CONTEXT
# ===================================================================

def generate_conversational_answer(
    generation_client: Any,
    question: str,
    chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate an answer to the ORIGINAL user question using
    retrieved context and the existing 3.40 citation pipeline.

    The rewritten query is used only for retrieval.
    """

    prompt, citation_map = build_cited_prompt(
        question,
        chunks,
    )

    answer = call_llm(
        generation_client,
        prompt,
    )

    citation_validation = validate_citations(
        answer,
        citation_map,
    )

    if not citation_validation["all_citations_valid"]:
        return {
            "answer": REFUSAL_MESSAGE,
            "sources": [],
            "citation_map": citation_map,
            "citation_validation": citation_validation,
            "fallback": True,
        }

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

    return {
        "answer": answer,
        "sources": sources,
        "citation_map": citation_map,
        "citation_validation": citation_validation,
        "fallback": False,
    }


# ===================================================================
# CONVERSATIONAL RAG
# ===================================================================

def conversational_answer(
    history: ConversationHistory,
    user_question: str,
    embedding_client: Any,
    generation_client: Any,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """
    Complete conversational RAG flow.

    1. Rewrite follow-up using history.
    2. Retrieve using rewritten query.
    3. Apply 3.41 hallucination guardrail.
    4. Generate grounded answer using original question.
    5. Validate citations.
    6. Append user/assistant turn to history.
    """

    # ---------------------------------------------------------------
    # STEP 1 — REWRITE FOLLOW-UP
    # ---------------------------------------------------------------

    standalone_query = rewrite_followup(
        generation_client,
        history,
        user_question,
    )

    # ---------------------------------------------------------------
    # STEP 2 — RETRIEVE USING REWRITTEN QUERY
    # ---------------------------------------------------------------

    chunks = retrieve_for_followup(
        embedding_client,
        standalone_query,
        k=top_k,
    )

    # ---------------------------------------------------------------
    # STEP 3 — APPLY 3.41 HALLUCINATION GUARDRAIL
    # ---------------------------------------------------------------

    retrieval_quality = evaluate_retrieval(
        chunks,
        min_top_score=MIN_TOP_SCORE,
        min_supporting_chunks=MIN_SUPPORTING_CHUNKS,
    )

    if not retrieval_quality["strong"]:

        answer = REFUSAL_MESSAGE

        history.add_turn(
            user_question,
            answer,
        )

        return {
            "status": "refused_weak_context",
            "question": user_question,
            "rewritten_query": standalone_query,
            "answer": answer,
            "sources": [],
            "retrieved_chunks": chunks,
            "retrieval_quality": retrieval_quality,
            "fallback": True,
        }

    # ---------------------------------------------------------------
    # STEP 4 — GENERATE GROUNDED ANSWER
    # ---------------------------------------------------------------

    generation_result = generate_conversational_answer(
        generation_client,
        user_question,
        chunks,
    )

    answer = generation_result["answer"]

    # ---------------------------------------------------------------
    # STEP 5 — UPDATE CONVERSATION HISTORY
    # ---------------------------------------------------------------

    history.add_turn(
        user_question,
        answer,
    )

    return {
        "status": (
            "answered"
            if not generation_result["fallback"]
            else "refused_invalid_citation"
        ),
        "question": user_question,
        "rewritten_query": standalone_query,
        "answer": answer,
        "sources": generation_result["sources"],
        "retrieved_chunks": chunks,
        "retrieval_quality": retrieval_quality,
        "citation_validation": (
            generation_result["citation_validation"]
        ),
        "fallback": generation_result["fallback"],
    }


# ===================================================================
# DISPLAY HELPERS
# ===================================================================

def print_retrieved_context(
    chunks: list[dict[str, Any]],
) -> None:
    """
    Print retrieved context for demo evidence.
    """

    print("Retrieved context:")

    if not chunks:
        print("  No chunks retrieved.")
        return

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):

        source = chunk.get(
            "source",
            "unknown",
        )

        chunk_id = chunk.get(
            "chunk_id",
            "unknown",
        )

        score = float(
            chunk.get(
                "score",
                0.0,
            )
        )

        text = chunk.get(
            "text",
            "",
        )

        print(
            f"  [{index}] "
            f"{source} | "
            f"chunk={chunk_id} | "
            f"score={score:.6f}"
        )

        print(
            f"      {text[:250]}"
        )


def print_result(
    turn_number: int,
    result: dict[str, Any],
) -> None:
    """
    Print one conversational RAG turn.
    """

    print("\n")
    print("=" * 70)
    print(
        f"TURN {turn_number}"
    )
    print("=" * 70)

    print(
        f"User question:\n"
        f"{result['question']}"
    )

    print(
        f"\nRewritten standalone query:\n"
        f"{result['rewritten_query']}"
    )

    quality = result["retrieval_quality"]

    print("\nRetrieval quality:")
    print(
        f"  Retrieved chunks       : "
        f"{quality['retrieval_count']}"
    )

    print(
        f"  Top score              : "
        f"{quality['top_score']:.6f}"
    )

    print(
        f"  Supporting chunks      : "
        f"{quality['supporting_chunks']}"
    )

    print(
        f"  Threshold              : "
        f"{quality['threshold']}"
    )

    print(
        f"  Retrieval accepted     : "
        f"{quality['strong']}"
    )

    print()

    print_retrieved_context(
        result["retrieved_chunks"]
    )

    print(
        f"\nFinal answer:\n"
        f"{result['answer']}"
    )

    print(
        f"\nStatus: "
        f"{result['status']}"
    )

    print(
        f"Sources: "
        f"{result['sources']}"
    )


# ===================================================================
# MULTI-TURN DEMO
# ===================================================================

def run_multi_turn_demo() -> None:
    """
    Demonstrate a multi-turn conversation where the second
    question depends on the first turn.
    """

    print("=" * 70)
    print("3.42 CONVERSATIONAL RAG & FOLLOW-UP CONTEXT")
    print("=" * 70)

    print("\nCONFIGURATION")
    print("-" * 70)

    print(
        f"Top-K retrieval            : "
        f"{TOP_K}"
    )

    print(
        f"Minimum relevance score   : "
        f"{MIN_TOP_SCORE}"
    )

    print(
        f"Minimum supporting chunks : "
        f"{MIN_SUPPORTING_CHUNKS}"
    )

    print(
        f"Maximum history tokens    : "
        f"{MAX_HISTORY_TOKENS}"
    )

    # ---------------------------------------------------------------
    # CLIENTS
    # ---------------------------------------------------------------

    embedding_client = create_embedding_client()

    generation_client = create_generation_client()

    # ---------------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------------

    history = ConversationHistory()

    # ---------------------------------------------------------------
    # TURN 1
    # ---------------------------------------------------------------

    first_question = (
        "When does an exporter need an export license?"
    )

    first_result = conversational_answer(
        history=history,
        user_question=first_question,
        embedding_client=embedding_client,
        generation_client=generation_client,
    )

    print_result(
        turn_number=1,
        result=first_result,
    )

    # ---------------------------------------------------------------
    # SHOW HISTORY AFTER TURN 1
    # ---------------------------------------------------------------

    print("\n")
    print("CONVERSATION HISTORY AFTER TURN 1")
    print("-" * 70)

    print(history.as_text())

    print(
        f"\nHistory tokens: "
        f"{history.token_count()}"
    )

    # ---------------------------------------------------------------
    # TURN 2 — FOLLOW-UP
    # ---------------------------------------------------------------

    second_question = (
        "What about the destination?"
    )

    second_result = conversational_answer(
        history=history,
        user_question=second_question,
        embedding_client=embedding_client,
        generation_client=generation_client,
    )

    print_result(
        turn_number=2,
        result=second_result,
    )

    # ---------------------------------------------------------------
    # SHOW UPDATED HISTORY
    # ---------------------------------------------------------------

    print("\n")
    print("CONVERSATION HISTORY AFTER TURN 2")
    print("-" * 70)

    print(history.as_text())

    print(
        f"\nHistory tokens: "
        f"{history.token_count()}"
    )

    # ---------------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------------

    turn1_answered = (
        first_result["status"] == "answered"
    )

    turn2_answered = (
        second_result["status"] == "answered"
    )

    turn1_has_rewrite = bool(
        first_result["rewritten_query"]
    )

    turn2_has_rewrite = bool(
        second_result["rewritten_query"]
    )

    turn2_query_is_not_raw = (
        second_result["rewritten_query"].strip().lower()
        != second_question.strip().lower()
    )

    turn2_has_context = bool(
        second_result["retrieved_chunks"]
    )

    turn2_has_sources = bool(
        second_result["sources"]
    )

    history_has_two_turns = (
        len(history) == 2
    )

    history_within_budget = (
        history.token_count()
        <= MAX_HISTORY_TOKENS
    )

    print("\n")
    print("VALIDATION CHECKS")
    print("-" * 70)

    print(
        f"turn1_answered             : "
        f"{turn1_answered}"
    )

    print(
        f"turn1_has_rewrite          : "
        f"{turn1_has_rewrite}"
    )

    print(
        f"turn2_answered             : "
        f"{turn2_answered}"
    )

    print(
        f"turn2_has_rewrite          : "
        f"{turn2_has_rewrite}"
    )

    print(
        f"turn2_query_rewritten      : "
        f"{turn2_query_is_not_raw}"
    )

    print(
        f"turn2_has_retrieved_context: "
        f"{turn2_has_context}"
    )

    print(
        f"turn2_has_sources          : "
        f"{turn2_has_sources}"
    )

    print(
        f"history_has_two_turns      : "
        f"{history_has_two_turns}"
    )

    print(
        f"history_within_token_budget: "
        f"{history_within_budget}"
    )

    all_checks = [
        turn1_answered,
        turn1_has_rewrite,
        turn2_answered,
        turn2_has_rewrite,
        turn2_query_is_not_raw,
        turn2_has_context,
        turn2_has_sources,
        history_has_two_turns,
        history_within_budget,
    ]

    print(
        f"\nALL CONVERSATIONAL RAG CHECKS PASS: "
        f"{all(all_checks)}"
    )


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:
    run_multi_turn_demo()


if __name__ == "__main__":
    main()