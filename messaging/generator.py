import json

from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message
from llm.protocol import LLMClient

HIRING_MANAGER_SYSTEM = """Write a LinkedIn connection request for a hiring manager. Rules:
- Under 300 characters total
- Reference they are hiring (do NOT say "I applied")
- Highlight 1-2 relevant skills from the job description
- Natural, confident tone
- Mention one SPECIFIC detail from their profile
- Return ONLY the message text, no quotes"""

RECRUITER_SYSTEM = """Write a LinkedIn connection request for an internal recruiter. Rules:
- Under 300 characters total
- Reference the open role at their company (do NOT say "I applied")
- Highlight 1 relevant skill from the job description
- Professional but warm tone
- Mention one SPECIFIC detail from their profile
- Return ONLY the message text, no quotes"""

PEER_SYSTEM = """Write a LinkedIn connection request for a professional peer. Rules:
- Under 300 characters total
- Do NOT mention any job or that you are applying anywhere
- Reference one SPECIFIC detail from their profile (role, company, career move, education, location)
- Focus only on relatability and genuine connection
- If no strong personalisation detail exists, respond with: SKIP
- Return ONLY the message text, no quotes"""

VETERAN_SYSTEM = """Write a LinkedIn connection request for a fellow veteran in tech. Rules:
- Under 300 characters total
- Acknowledge shared military background naturally
- Reference one SPECIFIC detail from their profile or military service
- Focus on connection and shared experience
- Return ONLY the message text, no quotes"""

SYSTEM_PROMPTS = {
    "hiring_manager": HIRING_MANAGER_SYSTEM,
    "recruiter": RECRUITER_SYSTEM,
    "peer": PEER_SYSTEM,
    "veteran": VETERAN_SYSTEM,
}


class MessageGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def generate(self, contact: Contact, job: Job):
        system = SYSTEM_PROMPTS.get(contact.category, PEER_SYSTEM)
        user = json.dumps(
            {
                "contact_name": contact.name,
                "contact_title": contact.title,
                "contact_company": contact.company,
                "contact_notes": contact.notes,
                "job_title": job.title,
                "job_description": job.raw_description,
            },
        )

        response = self.llm.complete(system=system, user=user)

        message = Message(
            job_id=job.id,
            contact_id=contact.id,
            message_text=response,
        )

        return message
