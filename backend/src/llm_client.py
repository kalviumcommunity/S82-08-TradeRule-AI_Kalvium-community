import logging

from openai import AuthenticationError, OpenAI, RateLimitError
from google import genai

from .config import GEMINI_API_KEY, CHAT_MODEL


logging.basicConfig(level=logging.INFO)


# ============================================================
# OPENAI-COMPATIBLE CLIENT
# Used by previous assignments: 3.12 - 3.16
# ============================================================

client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    timeout=60.0,
    max_retries=0,
)


# ============================================================
# GOOGLE GEMINI CLIENT
# Used for native structured output in Assignment 3.17
# ============================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# NORMAL MODEL REQUEST
# ============================================================

def ask_model(messages, **parameters):
    """
    Send a normal chat completion request using the
    OpenAI-compatible Gemini endpoint.

    This function is retained for previous assignments.
    """

    try:
        logging.info("REQUEST: %s", messages)
        logging.info("PARAMETERS: %s", parameters)

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            **parameters,
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

        raise Exception(
            f"LLM request failed: {error}"
        )


# ============================================================
# STRUCTURED MODEL REQUEST
# ============================================================

def ask_model_structured(response_model, question, system_prompt):
    """
    Request a structured JSON response from Gemini using
    the native Google GenAI SDK and a Pydantic model.

    Gemini's native structured-output support uses the
    Pydantic model as the response schema.
    """

    try:
        logging.info(
            "STRUCTURED REQUEST QUESTION: %s",
            question,
        )

        logging.info(
            "STRUCTURED RESPONSE MODEL: %s",
            response_model.__name__,
        )

        response = gemini_client.models.generate_content(
            model=CHAT_MODEL,
            contents=[
                system_prompt,
                question,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": response_model,
                "temperature": 0.0,
                "max_output_tokens": 500,
            },
        )

        logging.info(
            "STRUCTURED RAW RESPONSE: %s",
            response.text,
        )

        logging.info(
            "STRUCTURED RESPONSE: %s",
            response_model.model_validate_json(
                response.text
            ),
        )

        return response

    except Exception as error:
        logging.exception(
            "Structured Gemini request failed"
        )

        raise Exception(
            f"Structured Gemini request failed: {error}"
        )