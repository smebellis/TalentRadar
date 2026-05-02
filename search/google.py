import json
from datetime import datetime, timedelta, timezone

from db.models.job import Job
from llm.protocol import LLMClient
from search.filters import SearchFilters

SYSTEM_PROMPT = """You are an expert job recuiter with 20 years of experience finding qualified candidates for roles.  You will be given a set of keywords and a location. I want you to search google and find relevant jobs that match the keywords and location.  Return ONLY a valid JSON array like: [{'id': UUID, 'title': '', 'company': '', 'posted_at': datetime, 'source': 'google', 'apply_url': '', 'raw_description': '', 'fit_score': ''}] """


class GoogleJobSearcher:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def search(self, filters: SearchFilters) -> list:
        filter_string = filters.model_dump_json()
        response = self.llm.complete(system=SYSTEM_PROMPT, user=filter_string)
        response = response.strip()
        if response.startswith("```"):
            response = response.split("\n", 1)[1]
        if response.endswith("```"):
            response = response.rsplit("```", 1)[0]
        data = json.loads(response.strip())
        filtered_jobs = []
        for item in data:
            job = Job(
                title=item["title"],
                company=item["company"],
                posted_at=item["posted_at"],
                source="google",
                apply_url=item["apply_url"],
                raw_description=item["raw_description"],
            )
            if job.posted_at > datetime.now(timezone.utc) - timedelta(
                hours=filters.time_window_hours,
            ):
                filtered_jobs.append(job)
        return filtered_jobs
