import json
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends

from app.api.dependencies.auth import require_api_key
from app.api.schemas.ideas import (
    IdeaGenerationRequest,
    IdeaGenerationResponse,
    StoredIdeaRequest,
    TokenUsage,
)
from app.application.ideas.use_cases.generate_ideas import generate_ideas
from app.core.config import get_cache_ttl_days
from app.infrastructure.database.connection import get_db
from app.infrastructure.database.repositories.idea_repository import (
    find_idea_by_input,
    list_idea_requests,
    list_recent_ideas_for_user,
    save_idea,
)

router = APIRouter(tags=["ideas"])


@router.get("/api/")
def welcome():
    return {"message": "Welcome to the Idea Generator API"}


@router.post(
    "/api/",
    response_model=IdeaGenerationResponse,
    summary="Generate project ideas",
    description=(
        "Accepts structured metadata. Returns cached result if same metadata was already "
        "requested; otherwise generates ideas, stores the request, and returns them."
    ),
    dependencies=[Depends(require_api_key)],
)
@router.post("/", response_model=IdeaGenerationResponse, include_in_schema=False, dependencies=[Depends(require_api_key)])
@router.post("/api/generate_idea", response_model=IdeaGenerationResponse, include_in_schema=False, dependencies=[Depends(require_api_key)])
async def generate_idea(
    request: IdeaGenerationRequest,
    db: aiosqlite.Connection = Depends(get_db),
) -> IdeaGenerationResponse:
    ttl = get_cache_ttl_days()

    same_user_existing = await find_idea_by_input(
        db, request.prompt_template, request.metadata,
        user_id=request.user_id, model=request.model,
        temperature=request.temperature, number_of_ideas=request.number_of_ideas,
        ttl_days=ttl,
    )

    if same_user_existing is None:
        existing = await find_idea_by_input(
            db, request.prompt_template, request.metadata,
            model=request.model, temperature=request.temperature,
            number_of_ideas=request.number_of_ideas, ttl_days=ttl,
        )
        if existing is not None:
            return IdeaGenerationResponse(
                request_id=str(existing["id"]),
                user_id=request.user_id,
                prompt_template=request.prompt_template,
                metadata=request.metadata,
                ideas=json.loads(existing["ideas"]),
                usage=TokenUsage(
                    prompt_tokens=existing["prompt_tokens"],
                    completion_tokens=existing["completion_tokens"],
                    total_tokens=existing["total_tokens"],
                ),
                model=existing["model"],
                created_at=datetime.fromisoformat(existing["created_at"]),
            )

    previous_ideas = await list_recent_ideas_for_user(db, request.user_id)
    result = await generate_ideas(
        prompt_template=request.prompt_template,
        metadata=request.metadata,
        model=request.model,
        temperature=request.temperature,
        number_of_ideas=request.number_of_ideas,
        previous_ideas=previous_ideas,
    )

    now = datetime.now(timezone.utc).isoformat()
    record = await save_idea(
        db,
        user_id=request.user_id,
        metadata=request.metadata,
        prompt_template=request.prompt_template,
        request_model=request.model,
        request_temperature=request.temperature,
        request_number_of_ideas=request.number_of_ideas,
        ideas=json.dumps(result.ideas),
        model=result.model,
        prompt_tokens=result.usage.prompt_tokens,
        completion_tokens=result.usage.completion_tokens,
        total_tokens=result.usage.total_tokens,
        created_at=now,
        updated_at=now,
    )

    return IdeaGenerationResponse(
        request_id=str(record["id"]),
        user_id=record["user_id"],
        prompt_template=request.prompt_template,
        metadata=request.metadata,
        ideas=result.ideas,
        usage=TokenUsage(
            prompt_tokens=record["prompt_tokens"],
            completion_tokens=record["completion_tokens"],
            total_tokens=record["total_tokens"],
        ),
        model=record["model"],
        created_at=datetime.fromisoformat(record["created_at"]),
    )


@router.get(
    "/requests",
    response_model=list[StoredIdeaRequest],
    summary="List stored idea requests",
    description="Returns previously saved requests, generated ideas, and token usage.",
    dependencies=[Depends(require_api_key)],
)
async def get_requests(db: aiosqlite.Connection = Depends(get_db)) -> list[StoredIdeaRequest]:
    rows = await list_idea_requests(db)
    return [
        StoredIdeaRequest(
            request_id=str(row["id"]),
            user_id=row["user_id"],
            metadata=json.loads(row["metadata"]),
            ideas=json.loads(row["ideas"]),
            usage=TokenUsage(
                prompt_tokens=row["prompt_tokens"],
                completion_tokens=row["completion_tokens"],
                total_tokens=row["total_tokens"],
            ),
            model=row["model"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]

