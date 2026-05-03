import json
from datetime import datetime, timedelta, timezone

from db.models.job import Job
from search.filters import SearchFilters
from utils.logger import get_logger

logger = get_logger(__name__)

_SYSTEM = (
    "You are a job search assistant. Return ONLY a JSON array of job objects. "
    "Each object must have: title, company, posted_at (ISO 8601), apply_url, raw_description. "
    "No markdown, no explanation — raw JSON only."
)


class GoogleJobSearcher:
    def __init__(self, llm) -> None:
        self.llm = llm

    def search(self, filters: SearchFilters) -> list:
        user_payload = json.dumps({"keywords": filters.keywords, "location": filters.location})
        raw = self.llm.complete(system=_SYSTEM, user=user_payload)

        try:
            items = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("GoogleJobSearcher: LLM returned unparseable response.")
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=filters.time_window_hours)
        jobs: list[Job] = []
        for item in items:
            try:
                posted_at = datetime.fromisoformat(item["posted_at"])
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
                if posted_at < cutoff:
                    continue
                jobs.append(Job(
                    title=item["title"],
                    company=item["company"],
                    posted_at=posted_at,
                    source="google",
                    apply_url=item["apply_url"],
                    raw_description=item.get("raw_description", ""),
                ))
            except Exception:
                continue

        return jobs
