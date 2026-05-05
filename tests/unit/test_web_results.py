import pytest
from web.results import parse_jobs, parse_contacts


SAMPLE_OUTPUT = {
    "type": "a2ui",
    "version": "0.8",
    "job_table": {
        "columns": ["#", "role", "company", "score", "apply"],
        "rows": [
            {"role": "Data Engineer", "company": "Acme", "score": 8.5, "apply": "https://acme.com/jobs/1"},
            {"role": "ML Engineer", "company": "Globex", "score": 7.2, "apply": "https://globex.com/jobs/2"},
        ],
    },
    "contact_table": {
        "columns": ["#", "name", "title", "category", "relevance_score", "linkedin_url", "message"],
        "rows": [
            {
                "name": "Jane Smith",
                "title": "Sr. Recruiter",
                "category": "recruiter",
                "relevance_score": 9.0,
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "message": "Hi Jane, I noticed your work at Acme…",
            },
            {
                "name": "Bob Jones",
                "title": "Data Engineer",
                "category": "peer",
                "relevance_score": 7.5,
                "linkedin_url": "",
                "message": "",
            },
        ],
    },
    "priority_summary": [],
}


def test_parse_jobs_returns_rows():
    jobs = parse_jobs(SAMPLE_OUTPUT)
    assert len(jobs) == 2
    assert jobs[0]["role"] == "Data Engineer"
    assert jobs[1]["company"] == "Globex"


def test_parse_jobs_empty_when_missing():
    jobs = parse_jobs({})
    assert jobs == []


def test_parse_contacts_returns_rows():
    contacts = parse_contacts(SAMPLE_OUTPUT)
    assert len(contacts) == 2
    assert contacts[0]["name"] == "Jane Smith"
    assert contacts[0]["linkedin_url"] == "https://linkedin.com/in/janesmith"


def test_parse_contacts_message_embedded_in_contact():
    contacts = parse_contacts(SAMPLE_OUTPUT)
    assert contacts[0]["message"] == "Hi Jane, I noticed your work at Acme…"
    assert contacts[1]["message"] == ""


def test_parse_contacts_empty_when_missing():
    contacts = parse_contacts({})
    assert contacts == []
