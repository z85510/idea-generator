import re

from app.domain.ideas.entities import IdeaUsage


def normalize_idea_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def format_idea_memory(ideas: list[str], *, limit: int = 20) -> str:
    return "\n".join(f"- {idea}" for idea in ideas[:limit])


def filter_novel_ideas(
    ideas: list[str],
    *,
    excluded_ideas: list[str],
    expected_count: int,
) -> list[str]:
    seen = {normalize_idea_text(idea) for idea in excluded_ideas if normalize_idea_text(idea)}
    novel: list[str] = []

    for idea in ideas:
        normalized = normalize_idea_text(idea)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        novel.append(idea)
        if len(novel) >= expected_count:
            return novel

    return novel


def merge_usage(primary: IdeaUsage, secondary: IdeaUsage) -> IdeaUsage:
    def _sum(a: int | None, b: int | None) -> int | None:
        if a is None and b is None:
            return None
        return (a or 0) + (b or 0)

    return IdeaUsage(
        prompt_tokens=_sum(primary.prompt_tokens, secondary.prompt_tokens),
        completion_tokens=_sum(primary.completion_tokens, secondary.completion_tokens),
        total_tokens=_sum(primary.total_tokens, secondary.total_tokens),
    )

