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


def test_contact_finder_sets_company_from_job_not_vibe_response():
    people = [
        {
            "name": "Bob",
            "title": "Engineer",
            "linkedin_url": "https://linkedin.com/in/bob",
            "company": "OtherCorp",
            "email": None,
            "notes": "",
        },
    ]
    finder, _, _ = _make_finder(people)
    result = finder.find(_make_job())
    assert len(result) == 1
    assert result[0].company == "TechCorp"


def _make_person(name, title):
    return {
        "name": name,
        "title": title,
        "linkedin_url": f"https://linkedin.com/in/{name.lower()}",
        "company": "TechCorp",
        "email": None,
        "notes": "",
    }


def test_contact_finder_skips_executives():
    executives = [
        _make_person("Alice", "Chief Executive Officer"),
        _make_person("Bob", "SVP of Engineering"),
        _make_person("Carol", "Founder and CTO"),
        _make_person("Dave", "President"),
    ]
    finder, _, _ = _make_finder(executives)
    result = finder.find(_make_job())
    assert result == []


def test_contact_finder_does_not_skip_non_executives():
    people = [
        _make_person("Alice", "Engineering Manager"),
        _make_person("Bob", "Recruiter"),
        _make_person("Carol", "Data Scientist"),
    ]
    finder, _, _ = _make_finder(people)
    result = finder.find(_make_job())
    assert len(result) == 3


def test_contact_finder_categorizes_veteran_by_title():
    people = [_make_person("Dave", "Army Veteran turned Data Engineer")]
    finder, _, _ = _make_finder(people)
    result = finder.find(_make_job())
    assert len(result) == 1
    assert result[0].category == "veteran"
    assert result[0].is_veteran is True


def test_contact_finder_veteran_takes_priority_over_other_categories():
    people = [_make_person("Eve", "Military Veteran Recruiter")]
    finder, _, _ = _make_finder(people)
    result = finder.find(_make_job())
    assert result[0].category == "veteran"


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
