import tiktoken

from .llm_client import ask_model


enc = tiktoken.get_encoding("cl100k_base")


SYSTEM_PROMPT = (
    "You are TradeRule AI, an international shipment compliance assistant. "
    "Answer using only the information provided. "
    "Do not invent regulations or requirements."
)

PROMPT = """
A shipment contains lithium-ion batteries and is being transported internationally.

Based only on the information provided in this prompt, explain:
1. What compliance concern should the team consider?
2. What should the team verify before dispatch?

Keep the answer factual and concise.
"""


def run_experiment(name, **parameters):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": PROMPT},
    ]

    print("=" * 70)
    print(name)
    print("=" * 70)
    print(f"Parameters: {parameters}")

    response = ask_model(messages, **parameters)

    answer = response.choices[0].message.content

    print("\nOUTPUT:")
    print(answer)

    if response.usage:
        print("\nUSAGE:")
        print(response.usage)

    print()


def main():
    print("TRADE RULE AI — MODEL PARAMETERS & OUTPUT CONTROL")
    print()

    # Task 1 — Temperature
    run_experiment(
        "TEMPERATURE = 0.0",
        temperature=0.0,
    )

    run_experiment(
        "TEMPERATURE = 1.0",
        temperature=1.0,
    )

    # Task 2 — max_tokens
    run_experiment(
        "MAX TOKENS = 60",
temperature=0.1,
max_tokens=60,
    )

    # Task 3 — stop
    run_experiment(
        "STOP = ['\\n2.']",
        temperature=0.1,
        max_tokens=150,
        stop=["\n2."],
    )


if __name__ == "__main__":
    main()