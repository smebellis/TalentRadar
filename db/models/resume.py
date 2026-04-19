from pydantic import BaseModel


class ResumeProfile(BaseModel):
    skills: list[str]
    experience_years: int
    seniority: str
    location: str
    is_veteran: bool = False
    summary: str
