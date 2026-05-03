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


CATEGORY_TITLE_SIGNALS = {
    "recruiter": ["recruiter", "talent acquisition", "talent partner", "sourcer"],
    "hiring_manager": [
        "engineering manager",
        "director of engineering",
        "vp of engineering",
        "head of engineering",
        "team lead",
        "tech lead",
    ],
    "peer": [],
}

VETERAN_SIGNALS = [
    "veteran",
    "army",
    "navy",
    "marines",
    "air force",
    "coast guard",
    "space force",
    "military",
    "sergeant",
    "captain",
    "lieutenant",
    "corporal",
    "specialist",
    "mos",
    "afsc",
]


def _infer_category(title: str) -> str:
    title_lower = title.lower()
    for category, signals in CATEGORY_TITLE_SIGNALS.items():
        if any(s in title_lower for s in signals):
            return category
    return "peer"


def _is_veteran_profile(title: str, notes: str = "") -> bool:
    combined = (title + " " + notes).lower()
    return any(signal in combined for signal in VETERAN_SIGNALS)


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
            if person.get("company", "").lower() != job.company.lower():
                continue
            category = _infer_category(person.get("title", ""))
            is_vet = _is_veteran_profile(person.get("title", ""))
            if is_vet:
                category = "veteran"

            if category_counts.get(category, 0) >= self.max_per_category:
                continue

            contacts.append(
                Contact(
                    name=person["name"],
                    title=person["title"],
                    company=job.company,
                    category=category,
                    linkedin_url=person["linkedin_url"],
                    email=person.get("email"),
                    relevance_score=7.5,
                    is_veteran=is_vet,
                    notes=person.get("notes", "")[:100],
                )
            )
            category_counts[category] = category_counts.get(category, 0) + 1

        return contacts
