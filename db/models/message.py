from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class Message(BaseModel):
    contact_id: UUID
    job_id: UUID
    message_text: str
    character_count: int = 0

    @model_validator(mode="after")
    def check_character_count(self) -> Self:
        character_count = len(self.message_text)
        self.character_count = character_count
        if character_count > 300:
            raise ValueError("Message Count exceeds 300 characters")
        return self
