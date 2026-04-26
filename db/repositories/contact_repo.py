from uuid import UUID

from asyncpg import Pool

from db.models.contact import Contact
from db.models.job import Job

INSERT_CONTACT = """
INSERT INTO contacts (id, job_id, name, company, category, linkedin_url, email, relevance_score, is_veteran, notes)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
ON CONFLICT (id) DO NOTHING
"""

SELECT_ALL_JOBS = "SELECT * FROM contacts ORDER BY relevance_score DESC"


class ContactRepository:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def save(self, contact: Contact, job_id: UUID) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                INSERT_CONTACT,
                contact.id,
                job_id,
                contact.name,
                contact.company,
                contact.category,
                contact.linkedin_url,
                contact.email,
                contact.relevance_score,
                contact.is_veteran,
                contact.notes,
            )

    async def get_all(self) -> list[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(SELECT_ALL_JOBS)
        return [dict(row) for row in rows]
