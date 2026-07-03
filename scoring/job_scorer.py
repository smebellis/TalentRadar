import json

from db.models.job import Job
from db.models.resume import ResumeProfile
from llm.protocol import LLMClient
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """Analyze a provided job description and resume to determine the degree of fit between them. Provide a concise explanation for the determined fit, referencing direct matches or gaps between the job requirements and the resume's content. Return ONLY a valide JSON object like: {"score": 8.0, "reason": "Strong Python match"}"""


class JobScorer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def score(self, jobs: list[Job], resume: ResumeProfile):
        job_to_sort = []
        for job in jobs:
            job_params = job.model_dump_json(include={"raw_description"})
            resume_params = resume.model_dump_json(
                include={"skills", "experience_years", "seniority"}
            )
            user = f"Job: {job_params}\nResume: {resume_params}"
            response = self.llm.complete(system=SYSTEM_PROMPT, user=str(user))
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1]
            if response.endswith("```"):
                response = response.rsplit("```", 1)[0]
            try:
                data = json.loads(response.strip())
                job.fit_score = float(data["score"])
            except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                logger.warning(
                    "JobScorer: unparseable score for %r at %r — skipping score",
                    job.title,
                    job.company,
                )
                job.fit_score = None
            job_to_sort.append(job)
        sorted_jobs = sorted(
            job_to_sort, key=lambda c: c.fit_score or 0, reverse=True
        )

        return sorted_jobs
