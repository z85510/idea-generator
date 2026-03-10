"""Migration 0001: add metadata_hash column + unique index and backfill existing rows."""

import json
from typing import TYPE_CHECKING

from cache_hash import metadata_hash as get_metadata_hash

if TYPE_CHECKING:
    import aiosqlite


async def apply(connection: "aiosqlite.Connection") -> None:
    """
    Add metadata_hash cache column and unique index.
    Safe to run on both fresh and existing databases.
    """
    cursor = await connection.execute(
        "SELECT name FROM pragma_table_info('idea_requests') WHERE name = 'metadata_hash'"
    )
    has_column = (await cursor.fetchone()) is not None
    await cursor.close()

    if not has_column:
        await connection.execute(
            "ALTER TABLE idea_requests ADD COLUMN metadata_hash TEXT"
        )
        await connection.commit()

        cursor = await connection.execute(
            "SELECT id, metadata FROM idea_requests WHERE metadata_hash IS NULL"
        )
        rows = await cursor.fetchall()
        await cursor.close()
        for row in rows:
            try:
                meta = json.loads(row[1])
                h = get_metadata_hash(meta)
                await connection.execute(
                    "UPDATE idea_requests SET metadata_hash = ? WHERE id = ?",
                    (h, row[0]),
                )
            except (json.JSONDecodeError, TypeError):
                continue
        await connection.commit()

    await connection.execute(
        """
        DELETE FROM idea_requests
        WHERE metadata_hash IS NOT NULL
          AND id NOT IN (
            SELECT MIN(id) FROM idea_requests
            WHERE metadata_hash IS NOT NULL
            GROUP BY metadata_hash
          )
        """
    )
    await connection.commit()

    await connection.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_idea_requests_metadata_hash
        ON idea_requests(metadata_hash)
        """
    )
    await connection.commit()
