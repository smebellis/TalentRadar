from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Type

from db.models.resume import ResumeProfile
from search.filters import SearchFilters


class PipelineState(Enum):
    IDLE = "idle"
    PARSE_RESUME = "parse_resume"
    SEARCHING = "searching"
    SEARCH_JOBS = "search_jobs"
    SCORING_JOBS = "scoring_jobs"
    LOADING_CV = "loading_cv"
    FINDING_CONTACTS = "finding_contacts"
    SCORING_CONTACTS = "scoring_contacts"
    GENERATE_MESSAGES = "generate_messages"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class PipelineContext:
    state: PipelineState = PipelineState.IDLE
    jobs: list = field(default_factory=list)
    contacts: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    resume: Optional[ResumeProfile] | None = None
    filters: Optional[SearchFilters] | None = None
