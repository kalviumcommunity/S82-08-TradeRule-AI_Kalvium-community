"""
Verification script for Assignment 3.18.

Checks that two different features use the same
central prompt template and correctly inject values.
"""

from prompts.answer import ANSWER_TEMPLATE

from .template_chat import build_chat_prompt
from .template_batch import build_batch_prompt


def main():
    context = "Export classification must be verified."
    question = "What should the exporter verify?"

    # --------------------------------------------------------
    # Feature 1
    # --------------------------------------------------------

    chat_prompt = build_chat_prompt(
        context=context,
        question=question,
    )

    # --------------------------------------------------------
    # Feature 2
    # --------------------------------------------------------

    batch_prompt = build_batch_prompt(
        context=context,
        question=question,
    )

    # --------------------------------------------------------
    # Verify both use the same template structure
    # --------------------------------------------------------

    assert chat_prompt == batch_prompt

    # Verify runtime injection
    assert context in chat_prompt
    assert question in chat_prompt

    # Verify placeholders were rendered
    assert "{context}" not in chat_prompt
    assert "{question}" not in chat_prompt

    print("=" * 70)
    print("PROMPT TEMPLATE VERIFICATION")
    print("=" * 70)

    print("\nShared template:")
    print("ANSWER_TEMPLATE")

    print("\nFeature 1:")
    print("template_chat.py")

    print("\nFeature 2:")
    print("template_batch.py")

    print("\nRuntime context:")
    print(context)

    print("\nRuntime question:")
    print(question)

    print("\nRendered prompt:")
    print(chat_prompt)

    print("\nRESULT:")
    print("PASS — both features generated identical prompts.")
    print("PASS — runtime values were injected.")
    print("PASS — template placeholders were replaced.")


if __name__ == "__main__":
    main()