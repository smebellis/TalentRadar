import asyncpg

CREATE_JOBS_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    posted_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    apply_url TEXT NOT NULL,
    raw_description TEXT NOT NULL,
    fit_score DOUBLE PRECISION
)
"""

CREATE_CONTACTS_TABLE = """
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    category TEXT NOT NULL,
    linkedin_url TEXT NOT NULL,
    email TEXT,
    relevance_score DOUBLE PRECISION NOT NULL,
    is_veteran BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT NOT NULL
)
"""

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    message_text TEXT NOT NULL,
    character_count INT NOT NULL
)
"""


async def create_pool(
    host: str,
    port: int,
    db: str,
    user: str,
    password: str,
    min_size: int = 2,
    max_size: int = 10,
):
    return await asyncpg.create_pool(
        host=host,
        port=port,
        database=db,
        user=user,
        password=password,
        min_size=min_size,
        max_size=max_size,
    )


async def ensure_schema(pool: asyncpg.Pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(CREATE_JOBS_TABLE)
        await conn.execute(CREATE_CONTACTS_TABLE)
        await conn.execute(CREATE_MESSAGES_TABLE)
