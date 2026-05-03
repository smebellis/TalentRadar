from datetime import datetime, timezone
from unittest.mock import MagicMock

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


def _make_finder(vibe_people, max_per_category=8):
    mock_apify = MagicMock()
    mock_vibe = MagicMock()
    mock_vibe.find_people.return_value = vibe_people
    return ContactFinder(
        apify_client=mock_apify,
        vibe_client=mock_vibe,
        max_per_category=max_per_category,
    ), mock_apify, mock_vibe


def test_contact_finder_calls_vibe_find_people():
    finder, mock_apify, mock_vibe = _make_finder([])
    finder.find(_make_job())
    mock_vibe.find_people.assert_called_once_with(
        company="TechCorp", job_title="Senior Engineer"
    )


def test_contact_finder_does_not_call_apify():
    finder, mock_apify, mock_vibe = _make_finder([])
    finder.find(_make_job())
    mock_apify.find_people.assert_not_called()


def test_contact_finder_returns_contacts_for_job():
    people = [
        {
            "name": "Jane",
            "title": "Engineering Manager",
            "linkedin_url": "https://linkedin.com/in/jane",
            "company": "TechCorp",
            "email": None,
            "notes": "denver, colorado",
        },
    ]
    finder, _, _ = _make_finder(people)
    result = finder.find(_make_job())
    assert len(result) >= 1


def test_contact_finder_only_includes_current_employees():
    people = [
        {
            "name": "Bob",
            "title": "Former Manager",
            "linkedin_url": "https://linkedin.com/in/bob",
            "company": "OtherCorp",
            "email": None,
            "notes": "",
        },
    ]
    finder, _, _ = _make_finder(people)
    result = finder.find(_make_job())
    for contact in result:
        assert contact.company == "TechCorp"


def test_contact_finder_respects_max_per_category():
    many_people = [
        {
            "name": f"Person {i}",
            "title": "Recruiter",
            "linkedin_url": f"https://linkedin.com/in/p{i}",
            "company": "TechCorp",
            "email": None,
            "notes": "",
        }
        for i in range(20)
    ]
    finder, _, _ = _make_finder(many_people, max_per_category=3)
    result = finder.find(_make_job())
    recruiters = [c for c in result if c.category == "recruiter"]
    assert len(recruiters) <= 3
