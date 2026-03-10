"""Migration 0002: replace unique metadata_hash index with a non-unique lookup index."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite


async def apply(connection: "aiosqlite.Connection") -> None:
    await connection.execute("DROP INDEX IF EXISTS idx_idea_requests_metadata_hash")
    await connection.commit()

    await connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_idea_requests_metadata_hash
        ON idea_requests(metadata_hash)
        """
    )
    await connection.commit()