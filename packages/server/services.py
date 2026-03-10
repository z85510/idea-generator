import json
import os
from dataclasses import dataclass
import re

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


def _normalize_idea_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _format_idea_memory(ideas: list[str], *, limit: int = 20) -> str:
    recent_ideas = ideas[:limit]
    return "\n".join(f"- {idea}" for idea in recent_ideas)


def _build_messages(
    request: IdeaGenerationRequest,
    num_ideas: int,
    *,
    previous_ideas: list[str] | None = None,
    excluded_ideas: list[str] | None = None,
) -> list[dict[str, str]]:
    response_shape = _build_response_shape(num_ideas)
    memory_block = ""
    if previous_ideas:
        memory_block = (
            " Previously generated ideas for this user to avoid repeating or closely "
            f"paraphrasing:\n{_format_idea_memory(previous_ideas)}"
        )

    replacement_block = ""
    if excluded_ideas:
        replacement_block = (
            "\nAdditional ideas that must not be repeated in this response:\n"
            f"{_format_idea_memory(excluded_ideas)}"
        )

    return [
        {
            "role": "system",
            "content": (
                request.prompt_template + " "
                f"Return valid JSON only in this shape: {response_shape}."
                " Ensure every idea is materially distinct from the others."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate exactly {num_ideas} ideas based on these user inputs. "
                "Keep each idea concise but clear. Inputs: "
                f"{json.dumps(request.metadata, ensure_ascii=False)}"
                f"{memory_block}{replacement_block}"
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

    return ideas


def _merge_usage(primary: TokenUsage, secondary: TokenUsage) -> TokenUsage:
    def _sum(value_a: int | None, value_b: int | None) -> int | None:
        if value_a is None and value_b is None:
            return None
        return (value_a or 0) + (value_b or 0)

    return TokenUsage(
        prompt_tokens=_sum(primary.prompt_tokens, secondary.prompt_tokens),
        completion_tokens=_sum(primary.completion_tokens, secondary.completion_tokens),
        total_tokens=_sum(primary.total_tokens, secondary.total_tokens),
    )


def _filter_novel_ideas(
    ideas: list[str],
    *,
    excluded_ideas: list[str],
    expected_count: int,
) -> list[str]:
    seen = {
        _normalize_idea_text(idea)
        for idea in excluded_ideas
        if _normalize_idea_text(idea)
    }
    novel_ideas: list[str] = []

    for idea in ideas:
        normalized_idea = _normalize_idea_text(idea)
        if not normalized_idea or normalized_idea in seen:
            continue

        seen.add(normalized_idea)
        novel_ideas.append(idea)
        if len(novel_ideas) >= expected_count:
            return novel_ideas

    return novel_ideas


async def _generate_ideas_once(
    request: IdeaGenerationRequest,
    *,
    api_key: str,
    effective_model: str,
    effective_temperature: float,
    num_ideas: int,
    previous_ideas: list[str],
    excluded_ideas: list[str],
) -> GeneratedIdeasResult:
    payload = {
        "model": effective_model,
        "messages": _build_messages(
            request,
            num_ideas,
            previous_ideas=previous_ideas,
            excluded_ideas=excluded_ideas,
        ),
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
    ideas = _normalize_ideas(parsed_payload, num_ideas)
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


async def generate_ideas(
    request: IdeaGenerationRequest,
    *,
    previous_ideas: list[str] | None = None,
) -> GeneratedIdeasResult:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured.",
        )

    effective_model = request.model or _default_model()
    effective_temperature = request.temperature if request.temperature is not None else _default_temperature()
    effective_number_of_ideas = request.number_of_ideas or _default_number_of_ideas()
    prior_ideas = previous_ideas or []

    initial_result = await _generate_ideas_once(
        request,
        api_key=api_key,
        effective_model=effective_model,
        effective_temperature=effective_temperature,
        num_ideas=effective_number_of_ideas,
        previous_ideas=prior_ideas,
        excluded_ideas=[],
    )

    novel_ideas = _filter_novel_ideas(
        initial_result.ideas,
        excluded_ideas=prior_ideas,
        expected_count=effective_number_of_ideas,
    )
    total_usage = initial_result.usage

    if len(novel_ideas) < effective_number_of_ideas:
        remaining_count = effective_number_of_ideas - len(novel_ideas)
        retry_result = await _generate_ideas_once(
            request,
            api_key=api_key,
            effective_model=effective_model,
            effective_temperature=effective_temperature,
            num_ideas=remaining_count,
            previous_ideas=prior_ideas,
            excluded_ideas=[*prior_ideas, *novel_ideas],
        )
        total_usage = _merge_usage(total_usage, retry_result.usage)
        novel_ideas.extend(
            _filter_novel_ideas(
                retry_result.ideas,
                excluded_ideas=[*prior_ideas, *novel_ideas],
                expected_count=remaining_count,
            )
        )

    if len(novel_ideas) < effective_number_of_ideas:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider repeated too many previously generated ideas. Please try again.",
        )

    return GeneratedIdeasResult(
        ideas=novel_ideas[:effective_number_of_ideas],
        usage=total_usage,
        model=initial_result.model,
    )