"""Deterministic hashing for LLM response cache keys."""

import hashlib
import json
from typing import Any


def metadata_hash(prompt_template: str, metadata: dict[str, Any]) -> str:
    """Deterministic hash for cache key. Normalizes JSON so key order does not matter."""
    normalized = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prompt_template + normalized).encode()).hexdigest()
