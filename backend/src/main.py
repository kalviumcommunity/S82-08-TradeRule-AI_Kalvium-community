"""TradeRule AI backend entry point."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .llm_client import ask_model

app = FastAPI(title="TradeRule AI Backend")


class ChatRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    """Return backend health status."""
    return {"status": "ok"}


@app.post("/chat")
def chat(request: ChatRequest):
    """Send a question to the LLM."""

    messages = [
        {
            "role": "system",
            "content": (
                "You are TradeRule AI, a concise "
                "international shipment compliance assistant."
            ),
        },
        {
            "role": "user",
            "content": request.question,
        },
    ]

    try:
        response = ask_model(messages)

        return {
            "answer": response.choices[0].message.content,
            "usage": response.usage.model_dump()
            if response.usage
            else None,
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )