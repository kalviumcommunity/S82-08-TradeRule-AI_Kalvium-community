from __future__ import annotations

import hashlib
import os
import time
from typing import Any


CACHE_TTL_SECONDS = int(
    os.getenv("CACHE_TTL_SECONDS", "900")
)

_cache: dict[str, dict[str, Any]] = {}


def normalize_question(question: str) -> str:
    """Normalize question text for stable cache keys."""
    return " ".join(
        question.strip().lower().split()
    )


def build_cache_key(
    question: str,
    settings: dict[str, Any] | None = None,
) -> str:
    """Build a stable cache key."""

    normalized_question = (
        normalize_question(question)
    )

    settings = settings or {}

    settings_text = "|".join(
        f"{key}={settings[key]}"
        for key in sorted(settings)
    )

    raw_key = (
        f"{normalized_question}|"
        f"{settings_text}"
    )

    return hashlib.sha256(
        raw_key.encode("utf-8")
    ).hexdigest()


def get_cached_answer(
    question: str,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Get a cached answer if it exists and is not expired."""

    key = build_cache_key(
        question,
        settings,
    )

    entry = _cache.get(key)

    if entry is None:
        return None

    age = time.time() - entry["created_at"]

    if age > CACHE_TTL_SECONDS:
        _cache.pop(key, None)
        return None

    return entry["value"]


def save_cached_answer(
    question: str,
    answer: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> str:
    """Save an answer in the cache."""

    key = build_cache_key(
        question,
        settings,
    )

    _cache[key] = {
        "created_at": time.time(),
        "value": answer,
    }

    return key


def clear_cache() -> None:
    """Clear all cached answers."""

    _cache.clear()


def cache_stats() -> dict[str, int]:
    """Return basic cache statistics."""

    now = time.time()

    expired_keys = [
        key
        for key, entry in _cache.items()
        if (
            now - entry["created_at"]
            > CACHE_TTL_SECONDS
        )
    ]

    for key in expired_keys:
        _cache.pop(key, None)

    return {
        "entries": len(_cache),
    }


# Compatibility aliases
def get_cached(
    question: str,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    return get_cached_answer(
        question,
        settings,
    )


def save_cached(
    question: str,
    value: dict[str, Any],
    settings: dict[str, Any] | None = None,
) -> str:
    return save_cached_answer(
        question,
        value,
        settings,
    )


def stats() -> dict[str, int]:
    return cache_stats()