from asyncpg import Pool

from db.models.message import Message

INSERT_MESSAGE = """
INSERT INTO messages (contact_id, job_id, message_text, character_count)
VALUES ($1, $2, $3, $4)
"""


class MessageRepository:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool

    async def save(self, message: Message) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                INSERT_MESSAGE,
                message.contact_id,
                message.job_id,
                message.message_text,
                message.character_count,
            )
