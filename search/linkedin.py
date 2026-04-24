from datetime import datetime, timedelta, timezone

from apify_client import ApifyClient

from db.models.job import Job
from search.filters import SearchFilters


class LinkedInJobSearcher:
    def __init__(self, api_token: str) -> None:
        self.apify_client = ApifyClient(api_token=api_token)

    def search(self, filters: SearchFilters) -> list:
        actor_client = self.apify_client.actor("curious_coder/linkedin-jobs-scraper")
        run = actor_client.call(
            run_input={
                "keywords": filters.keywords,
                "location": filters.location,
            }
        )
        dataset_id = run["defaultDatasetId"]
        dataset = self.apify_client.dataset(dataset_id)
        items = list(dataset.iterate_items())
        filtered_jobs = []
        for item in items:
            job = Job(
                title=item["title"],
                company=item["companyName"],
                posted_at=item["postedAt"],
                source="linkedin",
                apply_url=item["jobUrl"],
                raw_description=item["description"],
            )
            if job.posted_at > datetime.now(timezone.utc) - timedelta(
                hours=filters.time_window_hours,
            ):
                filtered_jobs.append(job)

        return filtered_jobs
