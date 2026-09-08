"""
Reusable prompt templates for TradeRule AI.

Keeping prompts in this module separates prompt design
from application/business logic.
"""


# ============================================================
# SHARED ANSWER TEMPLATE
# ============================================================

ANSWER_TEMPLATE = """
You are TradeRule AI, an international shipment compliance assistant.

Answer clearly, concisely, and factually.

Answer ONLY from the provided context.
Do not invent regulations, requirements, or sources.

If the answer cannot be determined from the context,
say that the information is insufficient.

Context:
{context}

Question:
{question}
""".strip()


# ============================================================
# TEMPLATE RENDER FUNCTION
# ============================================================

def render(template, **values):
    """
    Fill the named placeholders in a prompt template.

    Example:

        render(
            ANSWER_TEMPLATE,
            context="Shipment requires an export license.",
            question="Is an export license required?"
        )
    """

    return template.format(**values)