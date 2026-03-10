import json
import os
from datetime import datetime, timezone

import aiosqlite
from fastapi import APIRouter, Depends

from auth import require_api_key
from db import find_idea_by_input, get_db, list_idea_requests, save_idea
from models import IdeaGenerationRequest, IdeaGenerationResponse, StoredIdeaRequest
from services import generate_ideas


def _cache_ttl_days() -> int | None:
    raw = os.getenv("IDEAS_CACHE_TTL_DAYS", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None

router = APIRouter(
    dependencies=[Depends(require_api_key)],
    tags=["ideas"],
)


@router.post(
    "/",
    response_model=IdeaGenerationResponse,
    summary="Generate five project ideas",
    description=(
        "Accepts structured metadata from the frontend. If the same metadata was already "
        "requested (by anyone), returns the stored result; otherwise generates five ideas, "
        "stores the request and response, and returns them."
    ),
    response_description="The stored request data and the five generated ideas.",
)
@router.post("/generate_idea", response_model=IdeaGenerationResponse, include_in_schema=False)
async def generate_idea(
    request: IdeaGenerationRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    ttl = _cache_ttl_days()
    existing = await find_idea_by_input(db, request.prompt_template, request.metadata, ttl_days=ttl)
    if existing is not None:
        return IdeaGenerationResponse(
            request_id=str(existing["id"]),
            user_id=request.user_id,
            prompt_template=request.prompt_template,
            metadata=request.metadata,
            ideas=json.loads(existing["ideas"]),
            usage={
                "prompt_tokens": existing["prompt_tokens"],
                "completion_tokens": existing["completion_tokens"],
                "total_tokens": existing["total_tokens"],
            },
            model=existing["model"],
            created_at=datetime.fromisoformat(existing["created_at"]),
        )

    generation_result = await generate_ideas(request)
    now = datetime.now(timezone.utc).isoformat()
    idea_record = await save_idea(
        db,
        user_id=request.user_id,
        metadata=request.metadata,
        prompt_template=request.prompt_template,
        ideas=json.dumps(generation_result.ideas),
        model=generation_result.model,
        prompt_tokens=generation_result.usage.prompt_tokens,
        completion_tokens=generation_result.usage.completion_tokens,
        total_tokens=generation_result.usage.total_tokens,
        created_at=now,
        updated_at=now,
    )

    return IdeaGenerationResponse(
        request_id=str(idea_record["id"]),
        user_id=idea_record["user_id"],
        prompt_template=request.prompt_template,
        metadata=request.metadata,
        ideas=generation_result.ideas,
        usage={
            "prompt_tokens": idea_record["prompt_tokens"],
            "completion_tokens": idea_record["completion_tokens"],
            "total_tokens": idea_record["total_tokens"],
        },
        model=idea_record["model"],
        created_at=datetime.fromisoformat(idea_record["created_at"]),
    )


@router.get(
    "/requests",
    response_model=list[StoredIdeaRequest],
    summary="List stored idea requests",
    description="Returns previously saved requests, generated ideas, and token usage.",
    response_description="Saved idea-generation history ordered from newest to oldest.",
)
async def get_requests(db: aiosqlite.Connection = Depends(get_db)):
    rows = await list_idea_requests(db)
    return [
        StoredIdeaRequest(
            request_id=str(row["id"]),
            user_id=row["user_id"],
            metadata=json.loads(row["metadata"]),
            ideas=json.loads(row["ideas"]),
            usage={
                "prompt_tokens": row["prompt_tokens"],
                "completion_tokens": row["completion_tokens"],
                "total_tokens": row["total_tokens"],
            },
            model=row["model"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]