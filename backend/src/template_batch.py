"""
Feature 2 — Batch evaluation prompt path.

This feature reuses the exact same prompt template
used by the chat feature.
"""

from prompts.answer import ANSWER_TEMPLATE, render


def build_batch_prompt(context, question):
    """
    Build the prompt used by the batch evaluator.
    """

    return render(
        ANSWER_TEMPLATE,
        context=context,
        question=question,
    )


def main():
    examples = [
        {
            "context": (
                "Commercial invoices should contain the "
                "seller, buyer, goods description, value, "
                "and currency."
            ),
            "question": (
                "What information should be checked "
                "on a commercial invoice?"
            ),
        },
        {
            "context": (
                "An export license may be required depending "
                "on the product classification and destination."
            ),
            "question": (
                "When should an export license be checked?"
            ),
        },
    ]

    print("=" * 70)
    print("FEATURE 2 — BATCH EVALUATION PROMPTS")
    print("=" * 70)

    for index, example in enumerate(examples, start=1):

        prompt = build_batch_prompt(
            context=example["context"],
            question=example["question"],
        )

        print(
            f"\n--- BATCH EXAMPLE {index} ---"
        )

        print(prompt)


if __name__ == "__main__":
    main()