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
    if ttl_days is not None:
        sql = """
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
            WHERE metadata_hash = ?
              AND created_at > datetime('now', ?)
            LIMIT 1
            """
        args = (h, f"-{ttl_days} days")
    else:
        sql = """
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
            WHERE metadata_hash = ?
            LIMIT 1
            """
        args = (h,)
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
    """Insert idea request or skip if same metadata_hash exists (UPSERT cache write)."""
    h = metadata_hash(
        prompt_template,
        metadata,
        model=request_model,
        temperature=request_temperature,
        number_of_ideas=request_number_of_ideas,
    )
    await connection.execute(
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
        ON CONFLICT(metadata_hash) DO NOTHING
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
    await connection.commit()

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
        WHERE metadata_hash = ?
        LIMIT 1
        """,
        (h,),
    )
    row = await cursor.fetchone()
    await cursor.close()
    if row is None:
        raise RuntimeError("Failed to load saved idea record.")
    return dict(row)


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