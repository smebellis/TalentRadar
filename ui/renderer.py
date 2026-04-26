import json

from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message


class UIRenderer:
    def render(self, jobs: list[Job], contacts: list[Contact], messages: list[Message]) -> str:
        msg_by_contact = {str(m.contact_id): m.message_text for m in messages}

        job_rows = [
            {
                "role": j.title,
                "company": j.company,
                "posted": j.posted_at.strftime("%Y-%m-%d %H:%M UTC"),
                "source": j.source,
                "score": j.fit_score,
                "apply": j.apply_url,
            }
            for j in jobs
        ]

        contact_rows = [
            {
                "name": c.name,
                "title": c.title,
                "category": c.category,
                "relevance_score": c.relevance_score,
                "linkedin_url": c.linkedin_url,
                "email": c.email,
                "notes": c.notes,
                "message": msg_by_contact.get(str(c.id), ""),
            }
            for c in contacts
        ]

        priority_summary = [
            {
                "priority": i + 1,
                "name": c.name,
                "category": c.category,
                "why": f"{c.title} at {c.company} — relevance {c.relevance_score}",
            }
            for i, c in enumerate(contacts[:10])
        ]

        output = {
            "type": "a2ui",
            "version": "0.8",
            "job_table": {
                "columns": [
                    "#",
                    "role",
                    "company",
                    "posted",
                    "source",
                    "score",
                    "apply",
                ],
                "rows": job_rows,
            },
            "contact_table": {
                "columns": [
                    "#",
                    "name",
                    "title",
                    "category",
                    "relevance_score",
                    "linkedin_url",
                    "email",
                    "notes",
                    "message",
                ],
                "rows": contact_rows,
            },
            "priority_summary": priority_summary,
        }

        return json.dumps(output, indent=2, default=str)
