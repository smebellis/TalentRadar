from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from contacts.finder import ContactFinder
from db.models.job import Job


def _make_job():
    return Job(
        title="Senior Engineer",
        company="TechCorp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="Python role",
    )


def test_contact_finder_returns_contacts_for_job():
    mock_apify = MagicMock()
    mock_vibe = MagicMock()

    mock_apify.find_people.return_value = [
        {
            "name": "Jane",
            "title": "Engineering Manager",
            "linkedin_url": "https://linkedin.com/in/jane",
            "company": "TechCorp",
            "is_veteran": False,
            "email": None,
        },
    ]
    mock_vibe.enrich.return_value = []

    finder = ContactFinder(
        apify_client=mock_apify, vibe_client=mock_vibe, max_per_category=8
    )
    result = finder.find(_make_job())
    assert len(result) >= 1


def test_contact_finder_only_includes_current_employees():
    mock_apify = MagicMock()
    mock_vibe = MagicMock()
    mock_apify.find_people.return_value = [
        {
            "name": "Bob",
            "title": "Former Manager",
            "linkedin_url": "https://linkedin.com/in/bob",
            "company": "OtherCorp",
            "is_veteran": False,
            "email": None,
        },
    ]
    mock_vibe.enrich.return_value = []

    finder = ContactFinder(
        apify_client=mock_apify, vibe_client=mock_vibe, max_per_category=8
    )
    result = finder.find(_make_job())
    for contact in result:
        assert contact.company == "TechCorp"


def test_contact_finder_respects_max_per_category():
    mock_apify = MagicMock()
    mock_vibe = MagicMock()
    many_people = [
        {
            "name": f"Person {i}",
            "title": "Recruiter",
            "linkedin_url": f"https://linkedin.com/in/p{i}",
            "company": "TechCorp",
            "is_veteran": False,
            "email": None,
        }
        for i in range(20)
    ]
    mock_apify.find_people.return_value = many_people
    mock_vibe.enrich.return_value = []

    finder = ContactFinder(
        apify_client=mock_apify, vibe_client=mock_vibe, max_per_category=3
    )
    result = finder.find(_make_job())
    recruiters = [c for c in result if c.category == "recruiter"]
    assert len(recruiters) <= 3
