import json

import httpx
from fastapi import HTTPException, status

from app.domain.ideas.entities import GeneratedIdeasResult, IdeaUsage
from app.domain.ideas.rules import format_idea_memory


def _build_response_shape(num_ideas: int) -> str:
    ideas = [f'"idea {i}"' for i in range(1, num_ideas + 1)]
    return '{"ideas":[' + ",".join(ideas) + "]}"


def _build_messages(
    prompt_template: str,
    metadata: dict,
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
            f"paraphrasing:\n{format_idea_memory(previous_ideas)}"
        )
    replacement_block = ""
    if excluded_ideas:
        replacement_block = (
            "\nAdditional ideas that must not be repeated in this response:\n"
            f"{format_idea_memory(excluded_ideas)}"
        )
    return [
        {
            "role": "system",
            "content": (
                prompt_template + " "
                f"Return valid JSON only in this shape: {response_shape}."
                " Ensure every idea is materially distinct from the others."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate exactly {num_ideas} ideas based on these user inputs. "
                "Keep each idea concise but clear. Inputs: "
                f"{json.dumps(metadata, ensure_ascii=False)}"
                f"{memory_block}{replacement_block}"
            ),
        },
    ]


def _extract_json_payload(content: str) -> dict:
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


def _normalize_ideas(payload: dict, expected_count: int) -> list[str]:
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


async def generate_once(
    prompt_template: str,
    metadata: dict,
    *,
    api_key: str,
    model: str,
    temperature: float,
    num_ideas: int,
    previous_ideas: list[str],
    excluded_ideas: list[str],
) -> GeneratedIdeasResult:
    payload = {
        "model": model,
        "messages": _build_messages(
            prompt_template, metadata, num_ideas,
            previous_ideas=previous_ideas,
            excluded_ideas=excluded_ideas,
        ),
        "temperature": temperature,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

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

    parsed = _extract_json_payload(content)
    ideas = _normalize_ideas(parsed, num_ideas)
    usage_data = response_data.get("usage", {})

    return GeneratedIdeasResult(
        ideas=ideas,
        usage=IdeaUsage(
            prompt_tokens=usage_data.get("prompt_tokens"),
            completion_tokens=usage_data.get("completion_tokens"),
            total_tokens=usage_data.get("total_tokens"),
        ),
        model=str(response_data.get("model") or model),
    )

