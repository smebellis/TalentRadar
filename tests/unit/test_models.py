from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message
from db.models.resume import ResumeProfile


def test_resume_profile_stores_fields() -> None:
    profile = ResumeProfile(
        skills=["Python", "SQL"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Experienced engineer",
    )
    assert profile.skills == ["Python", "SQL"]
    assert profile.experience_years == 5
    assert profile.is_veteran is False


def test_resume_profile_is_veteran_defaults_false() -> None:
    profile = ResumeProfile(
        skills=[],
        experience_years=0,
        seniority="junior",
        location="Denver, CO",
        summary="",
    )
    assert profile.is_veteran is False


def test_resume_profile_rejects_wrong_type() -> None:
    with pytest.raises(ValidationError):
        ResumeProfile(
            skills="not a list",
            experience_years="five",
            seniority="senior",
            location="Denver, CO",
            summary="",
        )


def test_job_auto_generates_uuid():
    job = Job(
        title="Engineer",
        company="Acme",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
    )
    assert isinstance(job.id, UUID)


def test_job_fit_score_defaults_none():
    job = Job(
        title="Engineer",
        company="Acme",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
    )
    assert job.fit_score is None


def test_job_source_accepts_google_and_linkedin():
    for source in ("google", "linkedin"):
        job = Job(
            title="Engineer",
            company="Acme",
            posted_at=datetime.now(timezone.utc),
            source=source,
            apply_url="https://example.com",
            raw_description="desc",
        )
        assert job.source == source


def test_contact_auto_generates_uuid():
    contact = Contact(
        name="Jane",
        title="Manager",
        company="Acme",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.0,
        is_veteran=False,
        notes="Short note",
    )
    assert isinstance(contact.id, UUID)


def test_contact_email_defaults_none():
    contact = Contact(
        name="Jane",
        title="Manager",
        company="Acme",
        category="recruiter",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=7.5,
        is_veteran=False,
        notes="",
    )
    assert contact.email is None


def test_contact_accepts_all_four_categories():
    for category in ("veteran", "hiring_manager", "recruiter", "peer"):
        c = Contact(
            name="X",
            title="Y",
            company="Z",
            category=category,
            linkedin_url="https://linkedin.com/in/x",
            relevance_score=8.0,
            is_veteran=(category == "veteran"),
            notes="",
        )
        assert c.category == category


def test_message_calculates_character_count():
    from uuid import uuid4

    msg = Message(
        contact_id=uuid4(),
        job_id=uuid4(),
        message_text="Hello, this is a test message.",
    )
    assert msg.character_count == len("Hello, this is a test message.")


def test_message_truncates_text_over_300_chars():
    from uuid import uuid4

    msg = Message(
        contact_id=uuid4(),
        job_id=uuid4(),
        message_text="x" * 301,
    )
    assert len(msg.message_text) <= 300
    assert msg.character_count <= 300
