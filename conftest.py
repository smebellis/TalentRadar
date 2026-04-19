from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from db.models.contact import Contact
from db.models.job import Job
from db.models.resume import ResumeProfile


@pytest.fixture
def sample_resume():
    return ResumeProfile(
        skills=["Python", "SQL", "Machine Learning"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Experienced software engineer",
    )


@pytest.fixture
def sample_veteran_resume():
    return ResumeProfile(
        skills=["Leadership", "Python", "Data Analysis"],
        experience_years=8,
        seniority="senior",
        location="Denver, CO",
        is_veteran=True,
        summary="Army veteran turned software engineer",
    )


@pytest.fixture
def sample_job():
    return Job(
        title="Senior Software Engineer",
        company="Acme Corp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com/apply",
        raw_description="We need a senior Python engineer...",
    )


@pytest.fixture
def sample_contact():
    return Contact(
        name="Jane Smith",
        title="Engineering Manager",
        company="Acme Corp",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/janesmith",
        relevance_score=8.5,
        is_veteran=False,
        notes="Manages the platform team",
    )


@pytest.fixture
def fake_llm():
    mock = MagicMock()
    mock.complete = MagicMock(return_value='{"result": "ok"}')
    return mock
