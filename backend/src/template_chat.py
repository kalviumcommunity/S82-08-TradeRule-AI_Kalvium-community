"""
Feature 1 — Chat/CLI prompt path.

This feature uses the shared prompt template from prompts.answer.
"""

from prompts.answer import ANSWER_TEMPLATE, render


def build_chat_prompt(context, question):
    """
    Build the prompt used by the chat feature.
    """

    return render(
        ANSWER_TEMPLATE,
        context=context,
        question=question,
    )


def main():
    context = """
The shipment contains electronic components.
The exporter must verify the applicable export
classification and destination-country requirements.
""".strip()

    question = (
        "What should the exporter verify before dispatch?"
    )

    prompt = build_chat_prompt(
        context=context,
        question=question,
    )

    print("=" * 70)
    print("FEATURE 1 — CHAT PROMPT")
    print("=" * 70)

    print("\nRENDERED PROMPT:\n")
    print(prompt)


if __name__ == "__main__":
    main()