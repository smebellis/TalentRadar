import re
from datetime import datetime, timedelta, timezone

from apify_client import ApifyClient

from db.models.job import Job
from search.filters import SearchFilters


def _parse_posted_at(value) -> datetime:
    """Return a timezone-aware datetime from whatever LinkedIn/Apify gives us.

    Handles:
    - ISO strings:          "2026-04-30T12:00:00Z", "2026-04-30"
    - Unix timestamps (int/float): 1746000000
    - Relative strings:     "2 hours ago", "3 days ago", "1 week ago"
    - Anything else:        falls back to now (so the item is not filtered out)
    """
    now = datetime.now(timezone.utc)

    if value is None:
        return now

    # Numeric Unix timestamp (seconds)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return now

    value = str(value).strip()

    # ISO 8601 — fromisoformat handles microseconds, offsets, and date-only
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass

    # Relative strings: "N unit ago"
    m = re.match(
        r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", value, re.I
    )
    if m:
        n, unit = int(m.group(1)), m.group(2).lower()
        deltas = {
            "second": timedelta(seconds=n),
            "minute": timedelta(minutes=n),
            "hour": timedelta(hours=n),
            "day": timedelta(days=n),
            "week": timedelta(weeks=n),
            "month": timedelta(days=n * 30),
            "year": timedelta(days=n * 365),
        }
        return now - deltas.get(unit, timedelta(0))

    return now


class LinkedInJobSearcher:
    def __init__(self, api_token: str) -> None:
        self.apify_client = ApifyClient(api_token)

    def search(self, filters: SearchFilters) -> list:
        keywords = "%20".join(filters.keywords)
        location = filters.location.replace(", ", "%2C%20").replace(" ", "%20")
        search_url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keywords}&location={location}"
        )
        actor_client = self.apify_client.actor("curious_coder/linkedin-jobs-scraper")
        run = actor_client.call(run_input={"urls": [search_url], "count": 50})
        dataset_id = run["defaultDatasetId"]
        dataset = self.apify_client.dataset(dataset_id)
        items = list(dataset.iterate_items())

        cutoff = datetime.now(timezone.utc) - timedelta(hours=filters.time_window_hours)
        filtered_jobs: list[Job] = []
        for item in items:
            apply_url = item.get("applyUrl") or item.get("link") or item.get("jobUrl")
            if not apply_url:
                continue
            try:
                raw_posted = item.get("postedAt") or item.get("postedAtTimestamp")
                posted_at = _parse_posted_at(raw_posted)
                job = Job(
                    title=item.get("title") or "Unknown",
                    company=item.get("companyName") or "Unknown",
                    posted_at=posted_at,
                    source="linkedin",
                    apply_url=apply_url,
                    raw_description=item.get("descriptionText")
                    or item.get("description")
                    or "",
                )
            except Exception:
                continue
            if job.posted_at >= cutoff:
                filtered_jobs.append(job)

        return filtered_jobs
