import logging

from openai import OpenAI

from .config import GEMINI_API_KEY, CHAT_MODEL

logging.basicConfig(level=logging.INFO)

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=60.0,
    max_retries=0,
)

SYSTEM_PROMPT = """
You are TradeRule AI, an international shipment compliance assistant.

Your scope is limited to helping users understand shipment documentation,
routing requirements, restrictions, and compliance considerations.

Answer clearly and concisely using only the information provided in the
conversation or supplied context.

Do not invent regulations, requirements, citations, or legal conclusions.

If the available information is insufficient to answer confidently, say:
"I don't have enough information to answer that reliably."

Use a professional and factual tone. Keep answers under 150 words unless
the user explicitly asks for more detail.
""".strip()


PROMPTS = {
    "VAGUE": "What documents are needed for an international shipment?",
    "CLEAR": (
        "List the 5 most commonly required documents for an international "
        "shipment. For each document, give its name and one short sentence "
        "explaining its purpose. Keep the answer under 100 words and use "
        "bullet points."
    ),
}


def ask(prompt: str) -> str:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": prompt,
        },
    ]

    logging.info("REQUEST: %s", messages)

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=messages,
    )

    answer = response.choices[0].message.content

    logging.info("RESPONSE: %s", answer)
    logging.info("USAGE: %s", response.usage)

    return answer


def main():
    for name, prompt in PROMPTS.items():
        print(f"\n{'=' * 60}")
        print(f"{name} PROMPT")
        print("=" * 60)
        print(prompt)

        answer = ask(prompt)

        print("\nOUTPUT:")
        print(answer)

    print(f"\n{'=' * 60}")
    print("CHOSEN PROMPT")
    print("=" * 60)
    print(PROMPTS["CLEAR"])


if __name__ == "__main__":
    main()