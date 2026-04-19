from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Contact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    title: str
    company: str
    category: str
    linkedin_url: str
    email: str | None = None
    relevance_score: float
    is_veteran: bool = False
    notes: str
