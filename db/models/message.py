from uuid import UUID

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self


class Message(BaseModel):
    contact_id: UUID
    job_id: UUID
    message_text: str
    character_count: int = 0

    @model_validator(mode="after")
    def check_character_count(self) -> Self:
        if len(self.message_text) > 300:
            truncated = self.message_text[:300].rsplit(" ", 1)[0]
            self.message_text = truncated
        self.character_count = len(self.message_text)
        return self
