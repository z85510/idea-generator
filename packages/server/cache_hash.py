"""Deterministic hashing for LLM response cache keys."""

import hashlib
import json
from typing import Any


def metadata_hash(
    prompt_template: str,
    metadata: dict[str, Any],
    *,
    model: str | None = None,
    temperature: float | None = None,
    number_of_ideas: int | None = None,
) -> str:
    """Deterministic hash for cache key. Normalizes JSON so key order does not matter."""
    cache_payload: dict[str, Any] = {
        "prompt_template": prompt_template,
        "metadata": metadata,
    }

    if model is not None or temperature is not None or number_of_ideas is not None:
        cache_payload["generation_options"] = {
            "model": model,
            "temperature": temperature,
            "number_of_ideas": number_of_ideas,
        }

    normalized = json.dumps(cache_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode()).hexdigest()
