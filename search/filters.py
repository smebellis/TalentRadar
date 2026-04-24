from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    keywords: list[str] = Field(default_factory=list[str])
    location: str = ""
    time_window_hours: int = 24
