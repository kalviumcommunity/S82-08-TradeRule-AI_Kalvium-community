import json

from pydantic import BaseModel, ValidationError

from .llm_client import ask_model_structured


# ============================================================
# STRUCTURED RESPONSE SCHEMA
# ============================================================

class TradeRuleResponse(BaseModel):
    """
    Required structured response.

    The model must provide:
    - answer
    - source
    """

    answer: str
    source: str


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are TradeRule AI.

You are an international shipment compliance assistant.

Return only a structured response containing:

answer:
A short factual answer to the user's question.

source:
The source or context used for the answer.

Keep both values concise.

Do not add any additional fields.
Do not invent regulations.
"""


# ============================================================
# PARSE AND VALIDATE
# ============================================================

def parse_and_validate(raw):
    """
    Parse JSON text and validate it using Pydantic.

    Returns:
        (validated_data, None)

    or:

        (None, error_message)
    """

    # --------------------------------------------------------
    # Step 1: JSON parsing
    # --------------------------------------------------------

    try:
        data = json.loads(raw)

    except json.JSONDecodeError:
        return None, "malformed JSON"

    # --------------------------------------------------------
    # Step 2: JSON object validation
    # --------------------------------------------------------

    if not isinstance(data, dict):
        return None, "JSON response must be an object"

    # --------------------------------------------------------
    # Step 3: Required field validation
    # --------------------------------------------------------

    try:
        validated = TradeRuleResponse.model_validate(data)

    except ValidationError as error:
        return None, f"validation failed: {error}"

    # --------------------------------------------------------
    # Step 4: Return usable Python dictionary
    # --------------------------------------------------------

    return validated.model_dump(), None


# ============================================================
# REQUEST STRUCTURED ANSWER
# ============================================================

def request_structured_answer(question):
    """
    Request structured JSON from Gemini using native
    structured-output support.
    """

    response = ask_model_structured(
        response_model=TradeRuleResponse,
        question=question,
        system_prompt=SYSTEM_PROMPT,
    )

    # Gemini returns JSON text because we requested:
    #
    # response_mime_type = application/json

    return response.text


# ============================================================
# RECOVERY
# ============================================================

def retry_structured_answer(question):
    """
    Retry the structured request after malformed JSON
    or validation failure.
    """

    print(
        "\nRECOVERY: Retrying structured JSON request."
    )

    recovery_prompt = """
Return only a valid JSON object matching the required schema.

Required fields:

answer:
A short factual answer.

source:
A short source or context description.

Do not include markdown.
Do not include explanations outside the JSON object.
Do not add additional fields.
"""

    response = ask_model_structured(
        response_model=TradeRuleResponse,
        question=question,
        system_prompt=recovery_prompt,
    )

    return response.text


# ============================================================
# CASE 1
# VALID STRUCTURED OUTPUT
# ============================================================

def run_valid_case():

    print("=" * 70)
    print("CASE 1 — VALID STRUCTURED OUTPUT")
    print("=" * 70)

    question = (
        "What should be checked before an international "
        "shipment is dispatched?"
    )

    # --------------------------------------------------------
    # Request structured response
    # --------------------------------------------------------

    raw = request_structured_answer(question)

    print("\nRAW MODEL RESPONSE:")
    print(raw)

    # --------------------------------------------------------
    # Parse and validate
    # --------------------------------------------------------

    data, error = parse_and_validate(raw)

    if error:

        print(
            f"\nVALIDATION ERROR: {error}"
        )

        print(
            "\nAttempting structured recovery..."
        )

        recovered_raw = retry_structured_answer(
            question
        )

        print(
            "\nRECOVERED RAW RESPONSE:"
        )

        print(recovered_raw)

        recovered_data, recovery_error = (
            parse_and_validate(
                recovered_raw
            )
        )

        if recovery_error:

            print(
                f"\nRECOVERY FAILED: "
                f"{recovery_error}"
            )

            return

        print(
            "\nRECOVERED PARSED OBJECT:"
        )

        print(recovered_data)

        print(
            "\nRECOVERY SUCCESSFUL"
        )

        return

    # --------------------------------------------------------
    # Successful structured response
    # --------------------------------------------------------

    print(
        "\nPARSED OBJECT:"
    )

    print(data)

    print(
        "\nANSWER:"
    )

    print(data["answer"])

    print(
        "\nSOURCE:"
    )

    print(data["source"])


# ============================================================
# CASE 2
# MALFORMED JSON + RECOVERY
# ============================================================

def run_malformed_case():

    print(
        "\n" + "=" * 70
    )

    print(
        "CASE 2 — MALFORMED JSON AND RECOVERY"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # Deliberately malformed JSON.
    #
    # The closing } is intentionally missing.
    # --------------------------------------------------------

    malformed_raw = (
        '{"answer": "Verify shipment documents", '
        '"source": "Compliance checklist"'
    )

    print(
        "\nRAW MALFORMED RESPONSE:"
    )

    print(malformed_raw)

    # --------------------------------------------------------
    # Attempt to parse malformed JSON
    # --------------------------------------------------------

    data, error = parse_and_validate(
        malformed_raw
    )

    if error:

        print(
            f"\nDETECTED ERROR: {error}"
        )

        print(
            "Malformed JSON detected successfully."
        )

        # ----------------------------------------------------
        # Recovery request
        # ----------------------------------------------------

        question = (
            "What should be checked before an "
            "international shipment is dispatched?"
        )

        recovered_raw = retry_structured_answer(
            question
        )

        print(
            "\nRECOVERED RAW RESPONSE:"
        )

        print(recovered_raw)

        # ----------------------------------------------------
        # Validate recovered JSON
        # ----------------------------------------------------

        recovered_data, recovery_error = (
            parse_and_validate(
                recovered_raw
            )
        )

        if recovery_error:

            print(
                f"\nRECOVERY FAILED: "
                f"{recovery_error}"
            )

            return

        print(
            "\nRECOVERED PARSED OBJECT:"
        )

        print(recovered_data)

        print(
            "\nRECOVERY SUCCESSFUL"
        )

    else:

        print(
            "\nUNEXPECTED: malformed JSON "
            "passed validation."
        )


# ============================================================
# CASE 3
# MISSING REQUIRED FIELD
# ============================================================

def run_missing_field_case():

    print(
        "\n" + "=" * 70
    )

    print(
        "CASE 3 — MISSING REQUIRED FIELD"
    )

    print(
        "=" * 70
    )

    # --------------------------------------------------------
    # "source" is intentionally missing.
    # --------------------------------------------------------

    missing_field_raw = (
        '{"answer": '
        '"Verify shipment documentation before dispatch."}'
    )

    print(
        "\nRAW RESPONSE:"
    )

    print(
        missing_field_raw
    )

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

    data, error = parse_and_validate(
        missing_field_raw
    )

    if error:

        print(
            f"\nVALIDATION ERROR: {error}"
        )

        if "source" in error:

            print(
                "\nRequired field 'source' was "
                "correctly detected as missing."
            )

    else:

        print(
            "\nUNEXPECTED: missing field "
            "passed validation."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "TRADE RULE AI — STRUCTURED OUTPUT "
        "& JSON HANDLING"
    )

    print(
        "\nUsing Pydantic structured response schema:"
    )

    print(
        "  answer: str"
    )

    print(
        "  source: str"
    )

    run_valid_case()

    run_malformed_case()

    run_missing_field_case()


if __name__ == "__main__":
    main()