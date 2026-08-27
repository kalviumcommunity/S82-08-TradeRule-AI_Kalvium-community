"""TradeRule AI backend entry point."""

from fastapi import FastAPI

app = FastAPI(title="TradeRule AI Backend")


@app.get("/health")
def health() -> dict[str, str]:
    """Return backend health status."""
    return {"status": "ok"}