import os

import aiosqlite

from app.infrastructure.database.migrations import run_migrations


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

