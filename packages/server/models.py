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
                "Extra information": ["I am a software engineer", "I am a designer"],
            }
        },
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "user-1",
                "prompt_template": "You generate practical and creative project ideas.",
                "metadata": {
                    "What do you love": ["tech", "art"],
                    "What does the world need": ["mental health", "education"],
                    "What are you good at": ["design", "coding"],
                    "Extra information": ["I am a software engineer", "I am a designer"],
                },
            }
        }
    }


class TokenUsage(BaseModel):
    prompt_tokens: int | None = Field(default=None, description="Tokens used by the prompt.")
    completion_tokens: int | None = Field(default=None, description="Tokens used by the model response.")
    total_tokens: int | None = Field(default=None, description="Total tokens billed for the request.")


class IdeaGenerationResponse(BaseModel):
    request_id: str = Field(description="Database identifier for the stored request.")
    user_id: str = Field(description="User identifier passed in the request.")
    prompt_template: str = Field(description="Prompt template used to generate the ideas.")
    metadata: dict[str, list[str]] = Field(default_factory=dict, description="Original metadata submitted by the client.")
    ideas: list[str] = Field(default_factory=list, description="Five generated project ideas.")
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = Field(description="Model used to generate the ideas.")
    created_at: datetime = Field(description="UTC timestamp when the request was saved.")


class StoredIdeaRequest(BaseModel):
    request_id: str = Field(description="Database identifier for the stored request.")
    user_id: str = Field(description="User identifier passed in the request.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Original metadata submitted by the client.")
    ideas: list[str] = Field(default_factory=list, description="Stored generated project ideas.")
    usage: TokenUsage = Field(default_factory=TokenUsage)
    model: str = Field(description="Model used to generate the ideas.")
    created_at: datetime = Field(description="UTC timestamp when the request was saved.")