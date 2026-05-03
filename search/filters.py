from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    keywords: list[str] = Field(default_factory=list[str])
    location: str = ""
    time_window_hours: int = 96
    remote: bool = True
    onsite: bool = True
    job_type: str = "full_time"
