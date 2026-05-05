import logging

from db.models.contact import Contact
from db.models.job import Job

logger = logging.getLogger(__name__)


class _NoopApifyClient:
    def find_people(self, company: str, job_title: str) -> list[dict]:
        return []


class _NoopVibeClient:
    def find_people(self, company: str, job_title: str) -> list[dict]:
        return []

    def enrich(self, people: list[dict]) -> list[dict]:
        return people


EXECUTIVE_SIGNALS = [
    "chief", "ceo", "cto", "cfo", "coo", "ciso", "cpo",
    "svp", "evp", "executive vice president", "senior vice president",
    "president", "founder", "co-founder", "partner", "managing director",
    "general manager",
]

CATEGORY_TITLE_SIGNALS = {
    "recruiter": ["recruiter", "talent acquisition", "talent partner", "sourcer"],
    "hiring_manager": [
        "engineering manager",
        "software manager",
        "data manager",
        "director of engineering",
        "director of software",
        "director of data",
        "director of technology",
        "director, engineering",
        "director, data",
        "vp of engineering",
        "vp of technology",
        "vp, engineering",
        "head of engineering",
        "head of data",
        "head of technology",
        "team lead",
        "tech lead",
        "technical lead",
        "engineering lead",
    ],
}


def _is_executive(title: str) -> bool:
    title_lower = title.lower()
    return any(signal in title_lower for signal in EXECUTIVE_SIGNALS)


def _infer_category(title: str) -> str:
    title_lower = title.lower()
    for category, signals in CATEGORY_TITLE_SIGNALS.items():
        if any(s in title_lower for s in signals):
            return category
    return "peer"



class ContactFinder:
    def __init__(self, apify_client, vibe_client, max_per_category: int) -> None:
        self.apify_client = apify_client or _NoopApifyClient()
        self.vibe_client = vibe_client or _NoopVibeClient()
        self.max_per_category = max_per_category

    def find(self, job: Job):
        raw_people = (
            self.vibe_client.find_people(company=job.company, job_title=job.title)
            or []
        )
        logger.info("ContactFinder: %d people from Vibe for %r", len(raw_people), job.company)
        contacts: list[Contact] = []
        category_counts: dict[str, int] = {}

        for person in raw_people:
            title = person.get("title", "")

            if _is_executive(title):
                continue

            category = _infer_category(title)

            if category_counts.get(category, 0) >= self.max_per_category:
                continue

            contacts.append(
                Contact(
                    name=person["name"],
                    title=title,
                    company=job.company,
                    category=category,
                    linkedin_url=person["linkedin_url"],
                    email=person.get("email"),
                    relevance_score=7.5,
                    is_veteran=False,
                    notes=person.get("notes", "")[:100],
                )
            )
            category_counts[category] = category_counts.get(category, 0) + 1

        return contacts
