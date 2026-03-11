"""Schema migrations: applied in order on startup."""

from app.infrastructure.database.migrations.versions import (
    m_0001_add_metadata_hash,
    m_0002_relax_metadata_hash_uniqueness,
)

MIGRATIONS: list[tuple[str, object]] = [
    ("0001_add_metadata_hash", m_0001_add_metadata_hash.apply),
    ("0002_relax_metadata_hash_uniqueness", m_0002_relax_metadata_hash_uniqueness.apply),
]


async def run_migrations(connection) -> None:
    """Apply pending migrations in order, recording each in schema_migrations."""
    await connection.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY)"
    )
    await connection.commit()

    cursor = await connection.execute("SELECT name FROM schema_migrations")
    rows = await cursor.fetchall()
    await cursor.close()
    applied = {row[0] for row in rows}

    for name, func in MIGRATIONS:
        if name in applied:
            continue
        await func(connection)
        await connection.execute(
            "INSERT INTO schema_migrations (name) VALUES (?)", (name,)
        )
        await connection.commit()

