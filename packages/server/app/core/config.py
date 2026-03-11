import os


def get_openrouter_api_key() -> str | None:
    return os.getenv("OPENROUTER_API_KEY")


def get_default_model() -> str:
    return os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def get_default_temperature() -> float:
    raw = os.getenv("OPENROUTER_TEMPERATURE", "0.9").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.9


def get_default_number_of_ideas() -> int:
    raw = os.getenv("OUTPUT_NUMBER", "5").strip()
    try:
        value = int(raw)
    except ValueError:
        return 5
    return value if value > 0 else 5


def get_cache_ttl_days() -> int | None:
    raw = os.getenv("IDEAS_CACHE_TTL_DAYS", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def get_origin_allowlist() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "").strip()
    return [p.strip() for p in raw.split(",") if p.strip()]


def is_origin_allowed(origin: str | None, allowlist: list[str]) -> bool:
    if not origin or not origin.strip():
        return True
    if not allowlist:
        return True
    return origin.strip() in allowlist

