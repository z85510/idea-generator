from fastapi import HTTPException, status

from app.core.config import (
    get_default_model,
    get_default_number_of_ideas,
    get_default_temperature,
    get_openrouter_api_key,
)
from app.domain.ideas.entities import GeneratedIdeasResult
from app.domain.ideas.rules import filter_novel_ideas, merge_usage
from app.infrastructure.ai.openrouter_client import generate_once


async def generate_ideas(
    *,
    prompt_template: str,
    metadata: dict,
    model: str | None = None,
    temperature: float | None = None,
    number_of_ideas: int | None = None,
    previous_ideas: list[str] | None = None,
) -> GeneratedIdeasResult:
    api_key = get_openrouter_api_key()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OPENROUTER_API_KEY is not configured.",
        )

    effective_model = model or get_default_model()
    effective_temperature = temperature if temperature is not None else get_default_temperature()
    effective_count = number_of_ideas or get_default_number_of_ideas()
    prior_ideas = previous_ideas or []

    initial_result = await generate_once(
        prompt_template,
        metadata,
        api_key=api_key,
        model=effective_model,
        temperature=effective_temperature,
        num_ideas=effective_count,
        previous_ideas=prior_ideas,
        excluded_ideas=[],
    )

    novel_ideas = filter_novel_ideas(
        initial_result.ideas,
        excluded_ideas=prior_ideas,
        expected_count=effective_count,
    )
    total_usage = initial_result.usage

    if len(novel_ideas) < effective_count:
        remaining = effective_count - len(novel_ideas)
        retry_result = await generate_once(
            prompt_template,
            metadata,
            api_key=api_key,
            model=effective_model,
            temperature=effective_temperature,
            num_ideas=remaining,
            previous_ideas=prior_ideas,
            excluded_ideas=[*prior_ideas, *novel_ideas],
        )
        total_usage = merge_usage(total_usage, retry_result.usage)
        novel_ideas.extend(
            filter_novel_ideas(
                retry_result.ideas,
                excluded_ideas=[*prior_ideas, *novel_ideas],
                expected_count=remaining,
            )
        )

    if len(novel_ideas) < effective_count:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Provider repeated too many previously generated ideas. Please try again.",
        )

    return GeneratedIdeasResult(
        ideas=novel_ideas[:effective_count],
        usage=total_usage,
        model=initial_result.model,
    )

