from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    company: str
    posted_at: datetime
    source: str
    apply_url: str
    raw_description: str
    fit_score: float | None = None
