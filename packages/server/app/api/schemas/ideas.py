from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IdeaGenerationRequest(BaseModel):
    user_id: str = Field(description="Unique user identifier from the client application.")
    prompt_template: str = Field(description="Prompt template used to generate the ideas.")
    metadata: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Structured user inputs grouped by category.",
        json_schema_extra={
            "example": {
                "What do you love": ["tech", "art"],
                "What does the world need": ["mental health", "education"],
                "What are you good at": ["design", "coding"],
            }
        },
    )
    model: str | None = Field(
        default=None,
        description="Optional model override. If omitted, the server default is used.",
    )
    temperature: float | None = Field(
        default=None, ge=0, le=2,
        description="Optional sampling temperature override.",
    )
    number_of_ideas: int | None = Field(
        default=None, ge=1, le=20,
        description="Optional number of ideas to generate.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user-1",
                "prompt_template": "Act as a creative product designer. Generate unique project titles.",
                "metadata": {
                    "What do you love": ["tech", "art"],
                    "What does the world need": ["mental health", "education"],
                    "What are you good at": ["design", "coding"],
                },
                "model": "openai/gpt-4o-mini",
                "temperature": 0.9,
                "number_of_ideas": 5,
            }
        }
    }


class TokenUsage(BaseModel):
    prompt_tokens: int | None = Field(default=None, description="Tokens used by the prompt.")
    completion_tokens: int | None = Field(default=None, description="Tokens used by the model response.")
    total_tokens: int | None = Field(default=None, description="Total tokens billed.")


class IdeaGenerationResponse(BaseModel):
    request_id: str = Field(description="Database identifier for the stored request.")
    user_id: str = Field(description="User identifier passed in the request.")
    prompt_template: str = Field(description="Prompt template used to generate the ideas.")
    metadata: dict[str, list[str]] = Field(default_factory=dict)
    ideas: list[str] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = Field(description="Model used to generate the ideas.")
    created_at: datetime = Field(description="UTC timestamp when the request was saved.")


class StoredIdeaRequest(BaseModel):
    request_id: str = Field(description="Database identifier for the stored request.")
    user_id: str = Field(description="User identifier passed in the request.")
    metadata: dict[str, Any] = Field(default_factory=dict)
    ideas: list[str] = Field(default_factory=list)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = Field(description="Model used to generate the ideas.")
    created_at: datetime = Field(description="UTC timestamp when the request was saved.")

