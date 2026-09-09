import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


# ------------------------------------------------------------
# API CONFIGURATION
# ------------------------------------------------------------

API_BASE_URL = os.getenv(
    "API_BASE_URL"
)

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

CHAT_MODEL = os.getenv(
    "CHAT_MODEL"
)


# ------------------------------------------------------------
# EMBEDDING CONFIGURATION
# ------------------------------------------------------------

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "gemini-embedding-001",
)

EMBEDDING_BASE_URL = os.getenv(
    "EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com/v1beta/openai/",
)


# ------------------------------------------------------------
# VECTOR DATABASE
# ------------------------------------------------------------

QDRANT_URL = os.getenv(
    "QDRANT_URL"
)

QDRANT_API_KEY = os.getenv(
    "QDRANT_API_KEY"
)


# ------------------------------------------------------------
# REDIS
# ------------------------------------------------------------

REDIS_URL = os.getenv(
    "REDIS_URL"
)