from dataclasses import dataclass


@dataclass(slots=True)
class IdeaUsage:
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


@dataclass(slots=True)
class GeneratedIdeasResult:
    ideas: list[str]
    usage: IdeaUsage
    model: str

