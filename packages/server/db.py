import json
import os
from typing import Any

import aiosqlite

from cache_hash import metadata_hash
from migrations import run_migrations


def get_database_path() -> str:
    return os.getenv("IDEAS_DB_PATH", "ideas.db")


async def init_db() -> None:
    async with aiosqlite.connect(get_database_path()) as connection:
        await connection.execute(
            """
            CREATE TABLE IF NOT EXISTS idea_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                metadata TEXT NOT NULL,
                metadata_hash TEXT,
                ideas TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER,
                completion_tokens INTEGER,
                total_tokens INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        await connection.commit()
        await run_migrations(connection)


async def get_db():
    async with aiosqlite.connect(get_database_path()) as connection:
        connection.row_factory = aiosqlite.Row
        yield connection


async def find_idea_by_input(
    connection: aiosqlite.Connection,
    prompt_template: str,
    metadata: dict[str, Any],
    *,
    user_id: str | None = None,
    model: str | None = None,
    temperature: float | None = None,
    number_of_ideas: int | None = None,
    ttl_days: int | None = None,
) -> dict[str, Any] | None:
    """Look up cached idea by deterministic metadata hash (indexed, fast)."""
    h = metadata_hash(
        prompt_template,
        metadata,
        model=model,
        temperature=temperature,
        number_of_ideas=number_of_ideas,
    )
    filters = ["metadata_hash = ?"]
    args: list[Any] = [h]

    if user_id is not None:
        filters.append("user_id = ?")
        args.append(user_id)

    if ttl_days is not None:
        filters.append("created_at > datetime('now', ?)")
        args.append(f"-{ttl_days} days")

    sql = f"""
            SELECT
                id,
                user_id,
                metadata,
                metadata_hash,
                ideas,
                model,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                created_at,
                updated_at
            FROM idea_requests
            WHERE {' AND '.join(filters)}
            ORDER BY id DESC
            LIMIT 1
            """
    cursor = await connection.execute(sql, args)
    row = await cursor.fetchone()
    await cursor.close()
    return dict(row) if row else None


async def save_idea(
    connection: aiosqlite.Connection,
    *,
    user_id: str,
    metadata: dict[str, Any],
    ideas: str,
    model: str,
    prompt_template: str,
    request_model: str | None = None,
    request_temperature: float | None = None,
    request_number_of_ideas: int | None = None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    total_tokens: int | None,
    created_at: str,
    updated_at: str,
) -> dict[str, Any]:
    """Insert a generated idea request as a new history row."""
    h = metadata_hash(
        prompt_template,
        metadata,
        model=request_model,
        temperature=request_temperature,
        number_of_ideas=request_number_of_ideas,
    )
    cursor = await connection.execute(
        """
        INSERT INTO idea_requests (
            user_id,
            metadata,
            metadata_hash,
            ideas,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            json.dumps(metadata),
            h,
            ideas,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            created_at,
            updated_at,
        ),
    )
    idea_id = cursor.lastrowid
    await cursor.close()
    await connection.commit()

    if idea_id is None:
        raise RuntimeError("Failed to save idea record.")

    cursor = await connection.execute(
        """
        SELECT
            id,
            user_id,
            metadata,
            metadata_hash,
            ideas,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            created_at,
            updated_at
        FROM idea_requests
        WHERE id = ?
        LIMIT 1
        """,
        (idea_id,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row is None:
        raise RuntimeError("Failed to load saved idea record.")
    return dict(row)


async def list_recent_ideas_for_user(
    connection: aiosqlite.Connection,
    user_id: str,
    *,
    request_limit: int = 20,
    idea_limit: int = 100,
) -> list[str]:
    cursor = await connection.execute(
        """
        SELECT ideas
        FROM idea_requests
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, request_limit),
    )
    rows = await cursor.fetchall()
    await cursor.close()

    collected_ideas: list[str] = []
    for row in rows:
        raw_ideas = row[0]
        try:
            parsed_ideas = json.loads(raw_ideas)
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(parsed_ideas, list):
            continue

        for idea in parsed_ideas:
            cleaned_idea = idea.strip() if isinstance(idea, str) else str(idea).strip()
            if not cleaned_idea:
                continue

            collected_ideas.append(cleaned_idea)
            if len(collected_ideas) >= idea_limit:
                return collected_ideas

    return collected_ideas


async def list_idea_requests(connection: aiosqlite.Connection) -> list[dict[str, Any]]:
    cursor = await connection.execute(
        """
        SELECT
            id,
            user_id,
            metadata,
            ideas,
            model,
            prompt_tokens,
            completion_tokens,
            total_tokens,
            created_at,
            updated_at
        FROM idea_requests
        ORDER BY id DESC
        """
    )
    rows = await cursor.fetchall()
    await cursor.close()
    return [dict(row) for row in rows]