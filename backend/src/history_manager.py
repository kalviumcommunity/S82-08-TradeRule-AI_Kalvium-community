import tiktoken

from .llm_client import ask_model


# Reuse the tokenizer approach from Assignment 3.14.
enc = tiktoken.get_encoding("cl100k_base")


SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are TradeRule AI, an international shipment compliance "
        "assistant. Answer clearly, concisely, and factually."
    ),
}


def count_tokens(messages):
    """Return the total token count for the current message history."""
    return sum(
        len(enc.encode(message["content"]))
        for message in messages
    )


def trim_history(messages, budget):
    """
    Remove the oldest non-system messages until the history
    fits within the token budget.
    """
    while count_tokens(messages) > budget and len(messages) > 1:
        removed = messages.pop(1)

        removed_tokens = len(enc.encode(removed["content"]))

        print(
            f"TRIMMED: {removed['role']} message "
            f"({removed_tokens} tokens)"
        )


def send_message(history, user_message, budget):
    """
    Add a user message, measure tokens, trim if necessary,
    call the model, and append the assistant response.
    """

    history.append({
        "role": "user",
        "content": user_message,
    })

    before_trim = count_tokens(history)

    print(f"REQUEST HISTORY TOKENS: {before_trim}")

    if before_trim > budget:
        print(f"BUDGET EXCEEDED: {budget} tokens")
        trim_history(history, budget)

    after_trim = count_tokens(history)

    print(f"TOKENS SENT TO MODEL: {after_trim}")

    response = ask_model(history)

    assistant_message = response.choices[0].message.content

    history.append({
        "role": "assistant",
        "content": assistant_message,
    })

    print(f"ASSISTANT: {assistant_message}")

    return assistant_message


def main():
    # Intentionally small budget so that trimming is demonstrated
    # during the sample conversation.
    budget = 250

    history = [SYSTEM_MESSAGE.copy()]

    conversation = [
        (
            "What documents are commonly required for an international "
            "shipment?"
        ),
        (
            "What is the purpose of a commercial invoice and what "
            "information does it normally contain?"
        ),
        (
            "Why is a packing list useful during customs clearance?"
        ),
        (
            "What is the difference between a bill of lading and an "
            "air waybill?"
        ),
        (
            "Why might a certificate of origin be required for an "
            "international shipment?"
        ),
        (
            "What additional documents might be required for restricted "
            "or regulated goods?"
        ),
        (
            "How can a compliance team verify that shipment documents "
            "are complete before dispatch?"
        ),
    ]

    print("=" * 70)
    print("TRADE RULE AI — CONTEXT HISTORY MANAGEMENT")
    print("=" * 70)
    print(f"Token budget: {budget}")

    for turn_number, message in enumerate(conversation, start=1):
        print(f"\n{'=' * 70}")
        print(f"TURN {turn_number}")
        print("=" * 70)

        send_message(history, message, budget)

        print(
            f"CURRENT HISTORY TOKENS: "
            f"{count_tokens(history)}"
        )


if __name__ == "__main__":
    main()
