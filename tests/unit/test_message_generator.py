from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message
from messaging.generator import MessageGenerator


def _make_job():
    return Job(
        title="Senior Engineer",
        company="TechCorp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="Looking for a Python expert with 5+ years experience",
    )


def _make_contact(category="hiring_manager"):
    return Contact(
        name="Jane Smith",
        title="Engineering Manager",
        company="TechCorp",
        category=category,
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.5,
        is_veteran=False,
        notes="Manages platform team",
    )


def _make_llm(response: str) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = response
    return mock


def test_message_generator_returns_message_object():
    llm = _make_llm("Hi Jane, saw you're building the platform team at TechCorp.")
    gen = MessageGenerator(llm=llm)
    result = gen.generate(_make_contact(), _make_job())
    assert isinstance(result, Message)


def test_message_generator_message_under_300_chars():
    llm = _make_llm("Short message under 300 chars.")
    gen = MessageGenerator(llm=llm)
    result = gen.generate(_make_contact(), _make_job())
    assert result.character_count <= 300


def test_message_generator_links_contact_and_job_ids():
    contact = _make_contact()
    job = _make_job()
    llm = _make_llm("Hi Jane, great opportunity.")
    gen = MessageGenerator(llm=llm)
    result = gen.generate(contact, job)
    assert result.contact_id == contact.id
    assert result.job_id == job.id


def test_message_generator_peer_message_does_not_mention_job():
    llm = _make_llm("Hey, saw your work on distributed systems — fascinating!")
    gen = MessageGenerator(llm=llm)
    contact = _make_contact(category="peer")
    result = gen.generate(contact, _make_job())
    assert isinstance(result, Message)
    llm.complete.assert_called_once()
    system_prompt_used = llm.complete.call_args.kwargs["system"]
    assert (
        "peer" in system_prompt_used.lower()
        or "do not mention" in system_prompt_used.lower()
    )


def test_message_generator_uses_job_description_for_skills():
    llm = _make_llm("Hi Jane, your Python experience aligns perfectly.")
    gen = MessageGenerator(llm=llm)
    gen.generate(_make_contact(), _make_job())
    user_payload = llm.complete.call_args.kwargs["user"]
    assert "Python" in user_payload
