import json
import os
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from models import IdeaGenerationRequest, TokenUsage


@dataclass(slots=True)
class GeneratedIdeasResult:
    ideas: list[str]
    usage: TokenUsage
    model: str


def _default_model() -> str:
    return os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


def _default_temperature() -> float:
    raw = os.getenv("OPENROUTER_TEMPERATURE", "0.9").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.9


def _default_number_of_ideas() -> int:
    raw = os.getenv("OUTPUT_NUMBER", "5").strip()
    try:
        value = int(raw)
    except ValueError:
        return 5
    return value if value > 0 else 5


def _build_response_shape(num_ideas: int) -> str:
    ideas = [f'"idea {index}"' for index in range(1, num_ideas + 1)]
    return '{"ideas":[' + ",".join(ideas) + ']}'


def _build_messages(request: IdeaGenerationRequest, num_ideas: int) -> list[dict[str, str]]:
    response_shape = _build_response_shape(num_ideas)
    return [
        {
            "role": "system",
            "content": (
                request.prompt_template + " "
                f"Return valid JSON only in this shape: {response_shape}."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate exactly {num_ideas} ideas based on these user inputs. "
                "Keep each idea concise but clear. Inputs: "
                f"{json.dumps(request.metadata, ensure_ascii=False)}"
            ),
        },
    ]


def _extract_json_payload(content: str) -> dict[str, object]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Provider returned an invalid response format.",
            )

        try:
            return json.loads(content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Provider returned a non-JSON ideas payload.",
            ) from exc


def _normalize_ideas(payload: dict[str, object], expected_count: int) -> list[str]:
    raw_ideas = payload.get("ideas")
    if not isinstance(raw_ideas, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider response did not include an ideas list.",
        )

    ideas: list[str] = []
    for item in raw_ideas:
        if isinstance(item, str):
            cleaned = item.strip()
        elif isinstance(item, dict):
            title = str(item.get("title", "")).strip()
            description = str(item.get("description", "")).strip()
            cleaned = ": ".join(part for part in [title, description] if part)
        else:
            cleaned = str(item).strip()

        if cleaned:
            ideas.append(cleaned)

    if len(ideas) < expected_count:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider returned fewer than {expected_count} ideas.",
        )

    return ideas[:expected_count]


async def generate_ideas(request: IdeaGenerationRequest) -> GeneratedIdeasResult:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured.",
        )

    effective_model = request.model or _default_model()
    effective_temperature = request.temperature if request.temperature is not None else _default_temperature()
    effective_number_of_ideas = request.number_of_ideas or _default_number_of_ideas()

    payload = {
        "model": effective_model,
        "messages": _build_messages(request, effective_number_of_ideas),
        "temperature": effective_temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )

    response.raise_for_status()
    response_data = response.json()

    try:
        content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected response from the idea provider.",
        ) from exc

    parsed_payload = _extract_json_payload(content)
    ideas = _normalize_ideas(parsed_payload, effective_number_of_ideas)
    usage_data = response_data.get("usage", {})

    return GeneratedIdeasResult(
        ideas=ideas,
        usage=TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens"),
            completion_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        ),
        model=str(response_data.get("model") or effective_model),
    )