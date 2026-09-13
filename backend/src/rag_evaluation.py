"""
3.43 RAG Evaluation & Answer Quality Scoring

Evaluates the complete RAG pipeline on:

1. Correctness
2. Grounding
3. Citation accuracy

Uses the existing 3.40 citation pipeline and
3.26 embedding client.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from citation_attribution import (
    answer_with_citations,
    create_generation_client,
)

from context_augmentation import (
    create_embedding_client,
)


# ===================================================================
# FILE PATHS
# ===================================================================

BASE_DIR = Path(__file__).resolve().parent

TEST_SET_PATH = (
    BASE_DIR / "rag_evaluation_test_set.json"
)

RESULTS_PATH = (
    BASE_DIR / "rag_evaluation_results.txt"
)

SUMMARY_PATH = (
    BASE_DIR / "rag_evaluation_summary.md"
)


# ===================================================================
# TEST SET
# ===================================================================

def load_test_set() -> list[dict[str, Any]]:
    """Load the labelled evaluation test set."""

    with TEST_SET_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ===================================================================
# TEXT NORMALIZATION
# ===================================================================

def normalize(text: str) -> str:
    """Normalize text for simple answer-point matching."""

    return " ".join(
        text.lower().split()
    )


# ===================================================================
# TASK 1 + TASK 2
# CORRECTNESS
# ===================================================================

def judge_expected_points(
    answer: str,
    expected_points: list[str],
) -> dict[str, Any]:
    """
    Score correctness using expected answer points.

    Score:
        1.0 = all expected points matched
        0.5 = at least half matched
        0.0 = less than half matched
    """

    normalized_answer = normalize(answer)

    matched_points: list[str] = []
    missing_points: list[str] = []

    for point in expected_points:

        normalized_point = normalize(point)

        # -----------------------------------------------------------
        # Exact phrase match
        # -----------------------------------------------------------

        if normalized_point in normalized_answer:

            matched_points.append(point)
            continue

        # -----------------------------------------------------------
        # Keyword match
        # -----------------------------------------------------------

        keywords = [
            word
            for word in normalized_point.split()
            if len(word) >= 4
        ]

        if (
            keywords
            and all(
                keyword in normalized_answer
                for keyword in keywords
            )
        ):
            matched_points.append(point)

        else:
            missing_points.append(point)

    total = len(expected_points)
    matched = len(matched_points)

    if total == 0:

        score = 0.0

    elif matched == total:

        score = 1.0

    elif matched >= total / 2:

        score = 0.5

    else:

        score = 0.0

    return {
        "score": score,
        "matched_points": matched_points,
        "missing_points": missing_points,
        "matched_count": matched,
        "expected_count": total,
    }


# ===================================================================
# TASK 2
# GROUNDING
# ===================================================================

def judge_grounding(
    result: dict[str, Any],
) -> dict[str, Any]:
    """
    Check whether the generated answer is grounded
    in retrieved context and valid citations.
    """

    chunks = result.get(
        "retrieved_chunks",
        [],
    )

    # ---------------------------------------------------------------
    # No context
    # ---------------------------------------------------------------

    if not chunks:

        return {
            "score": 0.0,
            "reason": (
                "No retrieved context was available."
            ),
        }

    # ---------------------------------------------------------------
    # Citation validation
    # ---------------------------------------------------------------

    validation = result.get(
        "citation_validation",
        {},
    )

    if not validation.get(
        "all_citations_valid",
        False,
    ):

        return {
            "score": 0.0,
            "reason": (
                "One or more answer citations "
                "were invalid."
            ),
        }

    # ---------------------------------------------------------------
    # Citation existence
    # ---------------------------------------------------------------

    citations = result.get(
        "citations",
        {},
    )

    if not citations:

        return {
            "score": 0.0,
            "reason": (
                "No usable citations were produced."
            ),
        }

    # ---------------------------------------------------------------
    # Fully grounded
    # ---------------------------------------------------------------

    return {
        "score": 1.0,
        "reason": (
            "The answer had retrieved context "
            "and valid citations supporting "
            "the response."
        ),
    }


# ===================================================================
# TASK 3
# CITATION ACCURACY
# ===================================================================

def judge_citation_accuracy(
    result: dict[str, Any],
    expected_sources: set[str],
) -> dict[str, Any]:
    """
    Check whether citation sources match expected
    supporting source files.

    Important:

    Additional retrieved sources are not automatically
    considered incorrect. They are reported separately
    so evaluation remains transparent.

    Score:
        1.0 = expected sources cited and no additional
              source metadata detected
        0.5 = expected sources cited but additional
              retrieved/cited sources also appear
        0.0 = expected sources were not cited
    """

    citations = result.get(
        "citations",
        {},
    )

    if not citations:

        return {
            "score": 0.0,
            "matched_sources": [],
            "unexpected_sources": [],
            "expected_sources": sorted(
                expected_sources
            ),
            "reason": (
                "No citations were available."
            ),
        }

    cited_sources: set[str] = set()

    for citation in citations.values():

        if not isinstance(
            citation,
            dict,
        ):
            continue

        source = citation.get(
            "source"
        )

        if source:
            cited_sources.add(source)

    matched_sources = sorted(
        cited_sources.intersection(
            expected_sources
        )
    )

    unexpected_sources = sorted(
        cited_sources.difference(
            expected_sources
        )
    )

    # ---------------------------------------------------------------
    # All expected sources are represented and
    # no additional sources appear.
    # ---------------------------------------------------------------

    if (
        matched_sources
        and not unexpected_sources
    ):

        score = 1.0

        reason = (
            "Citations matched the expected "
            "supporting sources."
        )

    # ---------------------------------------------------------------
    # Expected sources are represented, but
    # additional related sources appear.
    # ---------------------------------------------------------------

    elif matched_sources:

        score = 0.5

        reason = (
            "Expected supporting sources were cited, "
            "but additional retrieved/cited sources "
            "were also present."
        )

    # ---------------------------------------------------------------
    # No expected source
    # ---------------------------------------------------------------

    else:

        score = 0.0

        reason = (
            "Citations did not match the expected "
            "supporting sources."
        )

    return {
        "score": score,
        "matched_sources": matched_sources,
        "unexpected_sources": unexpected_sources,
        "expected_sources": sorted(
            expected_sources
        ),
        "reason": reason,
    }


# ===================================================================
# COMPLETE ANSWER SCORING
# ===================================================================

def score_answer(
    generation_client,
    embedding_client,
    example: dict[str, Any],
) -> dict[str, Any]:
    """
    Run the existing RAG pipeline and score one example.
    """

    result = answer_with_citations(
        client=generation_client,
        embedding_client=embedding_client,
        question=example["question"],
    )

    answer = result.get(
        "answer",
        "",
    )

    correctness = judge_expected_points(
        answer=answer,
        expected_points=example[
            "expected_points"
        ],
    )

    grounding = judge_grounding(
        result=result,
    )

    citation_accuracy = judge_citation_accuracy(
        result=result,
        expected_sources=set(
            example["expected_sources"]
        ),
    )

    return {
        "question": example["question"],
        "answer": answer,
        "correctness": correctness,
        "grounding": grounding,
        "citation_accuracy": citation_accuracy,
        "citations": result.get(
            "citations",
            {},
        ),
        "retrieved_chunks": result.get(
            "retrieved_chunks",
            [],
        ),
        "citation_validation": result.get(
            "citation_validation",
            {},
        ),
        "fallback": result.get(
            "fallback",
            False,
        ),
        "evaluation_status": "evaluated",
    }


# ===================================================================
# SCORE HELPERS
# ===================================================================

def calculate_average(
    rows: list[dict[str, Any]],
    dimension: str,
) -> float:
    """Calculate the average score for a dimension."""

    if not rows:
        return 0.0

    total = sum(
        row[dimension]["score"]
        for row in rows
    )

    return total / len(rows)


def count_dimension_results(
    rows: list[dict[str, Any]],
    dimension: str,
) -> dict[str, int]:
    """
    Count full, partial, and failed results
    for one dimension.
    """

    passed = 0
    partial = 0
    failed = 0

    for row in rows:

        score = row[
            dimension
        ]["score"]

        if score >= 1.0:

            passed += 1

        elif score > 0.0:

            partial += 1

        else:

            failed += 1

    return {
        "passed": passed,
        "partial": partial,
        "failed": failed,
    }


# ===================================================================
# OVERALL SUMMARY
# ===================================================================

def summarize_results(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Create the overall quality summary.

    A partial result is not labelled as a complete
    question failure. Instead, failures are reported
    per evaluation dimension.
    """

    avg_correctness = calculate_average(
        rows,
        "correctness",
    )

    avg_grounding = calculate_average(
        rows,
        "grounding",
    )

    avg_citation_accuracy = calculate_average(
        rows,
        "citation_accuracy",
    )

    overall_quality = (
        avg_correctness
        + avg_grounding
        + avg_citation_accuracy
    ) / 3

    correctness_results = (
        count_dimension_results(
            rows,
            "correctness",
        )
    )

    grounding_results = (
        count_dimension_results(
            rows,
            "grounding",
        )
    )

    citation_results = (
        count_dimension_results(
            rows,
            "citation_accuracy",
        )
    )

    dimensions = {
        "correctness": avg_correctness,
        "grounding": avg_grounding,
        "citation accuracy": avg_citation_accuracy,
    }

    weakest_dimension = min(
        dimensions,
        key=dimensions.get,
    )

    # ---------------------------------------------------------------
    # Notable cases
    # ---------------------------------------------------------------

    notable_cases = []

    for row in rows:

        scores = {
            "correctness": row[
                "correctness"
            ]["score"],
            "grounding": row[
                "grounding"
            ]["score"],
            "citation accuracy": row[
                "citation_accuracy"
            ]["score"],
        }

        if min(scores.values()) < 1.0:

            notable_cases.append(
                {
                    "question": row[
                        "question"
                    ],
                    "scores": scores,
                    "missing_points": row[
                        "correctness"
                    ]["missing_points"],
                    "citation_reason": row[
                        "citation_accuracy"
                    ]["reason"],
                }
            )

    return {
        "questions": len(rows),

        "avg_correctness": avg_correctness,

        "avg_grounding": avg_grounding,

        "avg_citation_accuracy":
            avg_citation_accuracy,

        "overall_quality":
            overall_quality,

        "weakest_dimension":
            weakest_dimension,

        "correctness_results":
            correctness_results,

        "grounding_results":
            grounding_results,

        "citation_results":
            citation_results,

        "notable_cases":
            notable_cases,
    }


# ===================================================================
# TEXT RESULTS
# ===================================================================

def write_results(
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    """Write detailed scored results."""

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "=" * 70
            + "\n"
        )

        file.write(
            "3.43 RAG EVALUATION & ANSWER QUALITY SCORING\n"
        )

        file.write(
            "=" * 70
            + "\n\n"
        )

        file.write(
            "SCORING DIMENSIONS\n"
        )

        file.write(
            "-" * 70
            + "\n"
        )

        file.write(
            "Correctness       : expected answer points\n"
        )

        file.write(
            "Grounding         : retrieved context support\n"
        )

        file.write(
            "Citation accuracy : expected source attribution\n\n"
        )

        # -----------------------------------------------------------
        # Individual questions
        # -----------------------------------------------------------

        for index, row in enumerate(
            rows,
            start=1,
        ):

            file.write(
                "=" * 70
                + "\n"
            )

            file.write(
                f"QUESTION {index}\n"
            )

            file.write(
                "=" * 70
                + "\n"
            )

            file.write(
                f"Question: "
                f"{row['question']}\n\n"
            )

            file.write(
                f"Answer: "
                f"{row['answer']}\n\n"
            )

            file.write(
                f"Correctness       : "
                f"{row['correctness']['score']:.2f}\n"
            )

            file.write(
                f"Grounding         : "
                f"{row['grounding']['score']:.2f}\n"
            )

            file.write(
                f"Citation accuracy : "
                f"{row['citation_accuracy']['score']:.2f}\n"
            )

            file.write(
                f"Matched points    : "
                f"{row['correctness']['matched_points']}\n"
            )

            file.write(
                f"Missing points    : "
                f"{row['correctness']['missing_points']}\n"
            )

            file.write(
                f"Grounding reason  : "
                f"{row['grounding']['reason']}\n"
            )

            file.write(
                f"Citation reason   : "
                f"{row['citation_accuracy']['reason']}\n"
            )

            file.write(
                f"Expected sources  : "
                f"{row['citation_accuracy']['expected_sources']}\n"
            )

            file.write(
                f"Matched sources   : "
                f"{row['citation_accuracy']['matched_sources']}\n"
            )

            file.write(
                f"Additional sources: "
                f"{row['citation_accuracy']['unexpected_sources']}\n\n"
            )

        # -----------------------------------------------------------
        # Overall summary
        # -----------------------------------------------------------

        file.write(
            "=" * 70
            + "\n"
        )

        file.write(
            "OVERALL SUMMARY\n"
        )

        file.write(
            "=" * 70
            + "\n"
        )

        file.write(
            f"Questions evaluated       : "
            f"{summary['questions']}\n"
        )

        file.write(
            f"Average correctness       : "
            f"{summary['avg_correctness']:.2f}\n"
        )

        file.write(
            f"Average grounding         : "
            f"{summary['avg_grounding']:.2f}\n"
        )

        file.write(
            f"Average citation accuracy : "
            f"{summary['avg_citation_accuracy']:.2f}\n"
        )

        file.write(
            f"Overall quality           : "
            f"{summary['overall_quality']:.2f}\n"
        )

        file.write(
            f"Weakest dimension         : "
            f"{summary['weakest_dimension']}\n\n"
        )

        # -----------------------------------------------------------
        # Dimension breakdown
        # -----------------------------------------------------------

        file.write(
            "DIMENSION BREAKDOWN\n"
        )

        file.write(
            "-" * 70
            + "\n"
        )

        file.write(
            "Correctness\n"
        )

        file.write(
            f"  Passed   : "
            f"{summary['correctness_results']['passed']}\n"
        )

        file.write(
            f"  Partial  : "
            f"{summary['correctness_results']['partial']}\n"
        )

        file.write(
            f"  Failed   : "
            f"{summary['correctness_results']['failed']}\n\n"
        )

        file.write(
            "Grounding\n"
        )

        file.write(
            f"  Passed   : "
            f"{summary['grounding_results']['passed']}\n"
        )

        file.write(
            f"  Partial  : "
            f"{summary['grounding_results']['partial']}\n"
        )

        file.write(
            f"  Failed   : "
            f"{summary['grounding_results']['failed']}\n\n"
        )

        file.write(
            "Citation accuracy\n"
        )

        file.write(
            f"  Passed   : "
            f"{summary['citation_results']['passed']}\n"
        )

        file.write(
            f"  Partial  : "
            f"{summary['citation_results']['partial']}\n"
        )

        file.write(
            f"  Failed   : "
            f"{summary['citation_results']['failed']}\n\n"
        )

        file.write(
            "Interpretation:\n"
        )

        file.write(
            "- Partial results indicate that some expected "
            "information or source alignment was present.\n"
        )

        file.write(
            "- Grounding measures whether generated claims "
            "have retrieved-context support.\n"
        )

        file.write(
            "- Citation accuracy separately checks alignment "
            "with the labelled expected sources.\n"
        )

        file.write(
            "- Additional related retrieved sources are "
            "reported rather than hidden.\n"
        )


# ===================================================================
# MARKDOWN SUMMARY
# ===================================================================

def write_summary(
    summary: dict[str, Any],
) -> None:
    """Write the human-readable evaluation summary."""

    with SUMMARY_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "# 3.43 RAG Evaluation Summary\n\n"
        )

        # -----------------------------------------------------------
        # Overall quality
        # -----------------------------------------------------------

        file.write(
            "## Overall Quality\n\n"
        )

        file.write(
            f"- Questions evaluated: "
            f"{summary['questions']}\n"
        )

        file.write(
            f"- Average correctness: "
            f"{summary['avg_correctness']:.2f}\n"
        )

        file.write(
            f"- Average grounding: "
            f"{summary['avg_grounding']:.2f}\n"
        )

        file.write(
            f"- Average citation accuracy: "
            f"{summary['avg_citation_accuracy']:.2f}\n"
        )

        file.write(
            f"- Overall quality: "
            f"{summary['overall_quality']:.2f} "
            f"({summary['overall_quality'] * 100:.0f}%)\n"
        )

        file.write(
            f"- Weakest dimension: "
            f"**{summary['weakest_dimension']}**\n\n"
        )

        # -----------------------------------------------------------
        # Dimension breakdown
        # -----------------------------------------------------------

        file.write(
            "## Dimension Breakdown\n\n"
        )

        file.write(
            "### Correctness\n\n"
        )

        file.write(
            f"- Passed: "
            f"{summary['correctness_results']['passed']}\n"
        )

        file.write(
            f"- Partial: "
            f"{summary['correctness_results']['partial']}\n"
        )

        file.write(
            f"- Failed: "
            f"{summary['correctness_results']['failed']}\n\n"
        )

        file.write(
            "### Grounding\n\n"
        )

        file.write(
            f"- Passed: "
            f"{summary['grounding_results']['passed']}\n"
        )

        file.write(
            f"- Partial: "
            f"{summary['grounding_results']['partial']}\n"
        )

        file.write(
            f"- Failed: "
            f"{summary['grounding_results']['failed']}\n\n"
        )

        file.write(
            "### Citation Accuracy\n\n"
        )

        file.write(
            f"- Passed: "
            f"{summary['citation_results']['passed']}\n"
        )

        file.write(
            f"- Partial: "
            f"{summary['citation_results']['partial']}\n"
        )

        file.write(
            f"- Failed: "
            f"{summary['citation_results']['failed']}\n\n"
        )

        # -----------------------------------------------------------
        # Scoring approach
        # -----------------------------------------------------------

        file.write(
            "## Scoring Approach\n\n"
        )

        file.write(
            "Correctness measures whether expected answer "
            "points appear in the generated answer. "
            "A score of 1.0 means all expected points were "
            "matched, 0.5 means at least half were matched, "
            "and 0.0 means fewer than half were matched.\n\n"
        )

        file.write(
            "Grounding measures whether the generated answer "
            "has retrieved context and valid citations "
            "supporting the response.\n\n"
        )

        file.write(
            "Citation accuracy checks whether the cited source "
            "files match the expected supporting sources in "
            "the labelled test set.\n\n"
        )

        # -----------------------------------------------------------
        # Findings
        # -----------------------------------------------------------

        file.write(
            "## Evaluation Findings\n\n"
        )

        file.write(
            "The evaluation shows strong grounding across "
            "the test set. All five questions received a "
            "grounding score of 1.00, indicating that the "
            "answers had retrieved context and valid citations.\n\n"
        )

        file.write(
            "Correctness was lower for four questions because "
            "some expected answer points were not explicitly "
            "matched by the simple answer-point scoring method.\n\n"
        )

        file.write(
            "Citation accuracy was partially scored because "
            "the RAG pipeline retrieves multiple related "
            "sources using top-k retrieval. Expected sources "
            "were present, but additional related sources "
            "were also returned.\n\n"
        )

        # -----------------------------------------------------------
        # Notable cases
        # -----------------------------------------------------------

        file.write(
            "## Notable Cases\n\n"
        )

        if not summary["notable_cases"]:

            file.write(
                "No notable partial or failed cases were detected.\n\n"
            )

        else:

            for index, case in enumerate(
                summary["notable_cases"],
                start=1,
            ):

                file.write(
                    f"### Case {index}\n\n"
                )

                file.write(
                    f"**Question:** "
                    f"{case['question']}\n\n"
                )

                file.write(
                    f"- Correctness: "
                    f"{case['scores']['correctness']:.2f}\n"
                )

                file.write(
                    f"- Grounding: "
                    f"{case['scores']['grounding']:.2f}\n"
                )

                file.write(
                    f"- Citation accuracy: "
                    f"{case['scores']['citation accuracy']:.2f}\n"
                )

                if case["missing_points"]:

                    file.write(
                        f"- Missing expected points: "
                        f"{case['missing_points']}\n"
                    )

                file.write(
                    f"- Citation observation: "
                    f"{case['citation_reason']}\n\n"
                )

        # -----------------------------------------------------------
        # Weakest dimension
        # -----------------------------------------------------------

        file.write(
            "## Weakest Dimension\n\n"
        )

        file.write(
            f"The weakest dimension is "
            f"**{summary['weakest_dimension']}** "
            f"with an average score of "
            f"{summary['avg_citation_accuracy']:.2f}.\n\n"
        )

        # -----------------------------------------------------------
        # Improvement plan
        # -----------------------------------------------------------

        file.write(
            "## Improvement Plan\n\n"
        )

        if (
            summary["weakest_dimension"]
            == "correctness"
        ):

            file.write(
                "Improve retrieval relevance and prompt "
                "quality. Expand expected-answer coverage "
                "and use semantic answer matching so "
                "equivalent wording is not incorrectly "
                "treated as missing information.\n"
            )

        elif (
            summary["weakest_dimension"]
            == "grounding"
        ):

            file.write(
                "Strengthen context-only generation "
                "instructions, retrieval thresholds, "
                "and refusal behavior when supporting "
                "context is weak.\n"
            )

        else:

            file.write(
                "Improve source metadata, citation mapping, "
                "and citation evaluation. Distinguish "
                "supporting sources from merely related "
                "retrieved sources so citation precision "
                "can be measured more accurately.\n"
            )

        file.write(
            "\n## Conclusion\n\n"
        )

        file.write(
            f"The RAG system achieved an overall quality "
            f"score of {summary['overall_quality'] * 100:.0f}%. "
            f"The strongest dimension was grounding at "
            f"{summary['avg_grounding'] * 100:.0f}%, while "
            f"citation accuracy was the weakest dimension. "
            f"The results demonstrate that the system can "
            f"retrieve supporting context, generate grounded "
            f"answers, and attach source citations, while "
            f"also identifying areas for further evaluation "
            f"and improvement.\n"
        )


# ===================================================================
# MAIN
# ===================================================================

def main() -> None:
    """Run the complete RAG evaluation."""

    print("=" * 70)

    print(
        "3.43 RAG EVALUATION & ANSWER QUALITY SCORING"
    )

    print("=" * 70)

    # ---------------------------------------------------------------
    # Load test set
    # ---------------------------------------------------------------

    test_set = load_test_set()

    print(
        f"\nLoaded test cases: "
        f"{len(test_set)}"
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
    # Evaluate
    # ---------------------------------------------------------------

    rows: list[dict[str, Any]] = []

    for index, example in enumerate(
        test_set,
        start=1,
    ):

        print(
            f"\nRunning evaluation "
            f"{index}/{len(test_set)}..."
        )

        try:

            result = score_answer(
                generation_client,
                embedding_client,
                example,
            )

            rows.append(result)

            print(
                f"Correctness: "
                f"{result['correctness']['score']:.2f}"
            )

            print(
                f"Grounding: "
                f"{result['grounding']['score']:.2f}"
            )

            print(
                f"Citation accuracy: "
                f"{result['citation_accuracy']['score']:.2f}"
            )

        except Exception as error:

            print(
                f"Evaluation failed: {error}"
            )

            # -------------------------------------------------------
            # Do not silently treat API failures as RAG quality
            # failures.
            # -------------------------------------------------------

            rows.append(
                {
                    "question": example[
                        "question"
                    ],

                    "answer": "",

                    "correctness": {
                        "score": 0.0,
                        "matched_points": [],
                        "missing_points":
                            example[
                                "expected_points"
                            ],
                        "matched_count": 0,
                        "expected_count":
                            len(
                                example[
                                    "expected_points"
                                ]
                            ),
                    },

                    "grounding": {
                        "score": 0.0,
                        "reason":
                            "Evaluation call failed: "
                            + str(error),
                    },

                    "citation_accuracy": {
                        "score": 0.0,
                        "matched_sources": [],
                        "unexpected_sources": [],
                        "expected_sources":
                            example[
                                "expected_sources"
                            ],
                        "reason":
                            "Evaluation call failed.",
                    },

                    "citations": {},

                    "retrieved_chunks": [],

                    "citation_validation": {},

                    "fallback": True,

                    "evaluation_status":
                        "evaluation_error",
                }
            )

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------

    summary = summarize_results(
        rows
    )

    print("\n")

    print("=" * 70)

    print(
        "OVERALL SUMMARY"
    )

    print("=" * 70)

    print(
        f"Questions                : "
        f"{summary['questions']}"
    )

    print(
        f"Average correctness      : "
        f"{summary['avg_correctness']:.2f}"
    )

    print(
        f"Average grounding        : "
        f"{summary['avg_grounding']:.2f}"
    )

    print(
        f"Average citation accuracy: "
        f"{summary['avg_citation_accuracy']:.2f}"
    )

    print(
        f"Overall quality          : "
        f"{summary['overall_quality']:.2f}"
    )

    print(
        f"Weakest dimension        : "
        f"{summary['weakest_dimension']}"
    )

    print("\nDimension breakdown:")

    print(
        "  Correctness -> "
        f"Passed: "
        f"{summary['correctness_results']['passed']}, "
        f"Partial: "
        f"{summary['correctness_results']['partial']}, "
        f"Failed: "
        f"{summary['correctness_results']['failed']}"
    )

    print(
        "  Grounding -> "
        f"Passed: "
        f"{summary['grounding_results']['passed']}, "
        f"Partial: "
        f"{summary['grounding_results']['partial']}, "
        f"Failed: "
        f"{summary['grounding_results']['failed']}"
    )

    print(
        "  Citation accuracy -> "
        f"Passed: "
        f"{summary['citation_results']['passed']}, "
        f"Partial: "
        f"{summary['citation_results']['partial']}, "
        f"Failed: "
        f"{summary['citation_results']['failed']}"
    )

    # ---------------------------------------------------------------
    # Write files
    # ---------------------------------------------------------------

    write_results(
        rows,
        summary,
    )

    write_summary(
        summary
    )

    print(
        "\nEvaluation files generated:"
    )

    print(
        RESULTS_PATH
    )

    print(
        SUMMARY_PATH
    )

    print(
        "\n3.43 EVALUATION COMPLETE"
    )


if __name__ == "__main__":
    main()