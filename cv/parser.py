import json

from db.models.resume import ResumeProfile
from llm.protocol import LLMClient

SYSTEM_PROMPT = """You are a expert recuiter with a background in the military. You will receive a resume.  Extract the canidates veteran status, skills, experience, senority, location and summary and Return ONLY a valid JSON array like: ['skills': [str], 'experience_years': int, 'seniority': str, 'location': str, 'is_veteran': bool = False, 'summary': str"""


class CVParser:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def parse(self, resume_text: str) -> ResumeProfile:
        response = self.llm.complete(system=SYSTEM_PROMPT, user=resume_text)
        data = json.loads(response)

        resume = ResumeProfile(
            skills=data["skills"],
            experience_years=data["experience_years"],
            seniority=data["seniority"],
            location=data["location"],
            is_veteran=data["is_veteran"],
            summary=data["summary"],
        )

        return resume
