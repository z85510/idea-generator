"""
Schema migrations: applied in order on startup.
Add new migrations to MIGRATIONS and implement apply(connection) in versions/m_XXXX_*.py.
"""

from migrations.versions import m_0001_add_metadata_hash

# (name, apply_func) — name is stored in schema_migrations; apply_func(connection) is run once per name
MIGRATIONS: list[tuple[str, callable]] = [
    ("0001_add_metadata_hash", m_0001_add_metadata_hash.apply),
]


async def run_migrations(connection) -> None:
    """Apply pending migrations in order, recording each in schema_migrations."""
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY
        )
        """
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
            "INSERT INTO schema_migrations (name) VALUES (?)",
            (name,),
        )
        await connection.commit()
