import logging

from openai import AuthenticationError, OpenAI, RateLimitError

from .config import GEMINI_API_KEY, CHAT_MODEL

logging.basicConfig(level=logging.INFO)

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=30.0,
    max_retries=0,
)


def ask_model(messages):
    try:
        logging.info("REQUEST: %s", messages)

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
        )

        logging.info(
            "RESPONSE: %s",
            response.choices[0].message.content,
        )

        logging.info("USAGE: %s", response.usage)

        return response

    except AuthenticationError:
        logging.error("Gemini authentication failed")
        raise Exception(
            "Auth failed (401): check GEMINI_API_KEY in your .env"
        )

    except RateLimitError:
        logging.error("Gemini rate limit reached")
        raise Exception(
            "Rate limited (429): slow down and retry"
        )

    except Exception as error:
        logging.exception("LLM request failed")
        raise Exception(f"LLM request failed: {error}")