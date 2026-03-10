import json
import os
from dataclasses import dataclass

import httpx
from fastapi import HTTPException, status

from models import IdeaGenerationRequest, TokenUsage


DEFAULT_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")


@dataclass(slots=True)
class GeneratedIdeasResult:
    ideas: list[str]
    usage: TokenUsage
    model: str


def _build_messages(request: IdeaGenerationRequest) -> list[dict[str, str]]:
    num_ideas = os.getenv("OUTPUT_NUMBER", "5")
    response_shape = (
        f'{{"ideas":["idea 1","idea 2","idea 3","idea 4","idea {num_ideas}"]}}'
    )
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


def _normalize_ideas(payload: dict[str, object]) -> list[str]:
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

    if len(ideas) < 5:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider returned fewer than 5 ideas.",
        )

    return ideas[:5]


async def generate_ideas(request: IdeaGenerationRequest) -> GeneratedIdeasResult:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured.",
        )

    payload = {
        "model": DEFAULT_MODEL,
        "messages": _build_messages(request),
        "temperature": 0.9,
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
    ideas = _normalize_ideas(parsed_payload)
    usage_data = response_data.get("usage", {})

    return GeneratedIdeasResult(
        ideas=ideas,
        usage=TokenUsage(
            prompt_tokens=usage_data.get("prompt_tokens"),
            completion_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        ),
        model=str(response_data.get("model") or DEFAULT_MODEL),
    )