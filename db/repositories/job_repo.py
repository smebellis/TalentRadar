from asyncpg import Pool

from db.models.job import Job

INSERT_JOB = """
INSERT INTO jobs (id, title, company, posted_at, source, apply_url, raw_description, fit_score)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (id) DO NOTHING
"""

SELECT_ALL_JOBS = "SELECT * FROM jobs ORDER BY posted_at DESC"


class JobRepository:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def save(self, job: Job) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                INSERT_JOB,
                job.id,
                job.title,
                job.company,
                job.posted_at,
                job.source,
                job.apply_url,
                job.raw_description,
                job.fit_score,
            )

    async def get_all(self) -> list[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(SELECT_ALL_JOBS)
        return [dict(row) for row in rows]
