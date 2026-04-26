import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message
from ui.renderer import UIRenderer


def _make_job(score=8.5):
    return Job(
        title="Senior Engineer",
        company="TechCorp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
        fit_score=score,
    )


def _make_contact():
    return Contact(
        name="Jane Smith",
        title="Engineering Manager",
        company="TechCorp",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.5,
        is_veteran=False,
        notes="Manages platform team",
    )


def _make_message(contact_id, job_id):
    return Message(
        contact_id=contact_id,
        job_id=job_id,
        message_text="Hi Jane, saw you're hiring at TechCorp!",
    )


def test_renderer_returns_valid_json():
    renderer = UIRenderer()
    contact = _make_contact()
    job = _make_job()
    msg = _make_message(contact.id, job.id)
    output = renderer.render(jobs=[job], contacts=[contact], messages=[msg])
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_renderer_output_contains_job_table():
    renderer = UIRenderer()
    output = renderer.render(jobs=[_make_job()], contacts=[], messages=[])
    parsed = json.loads(output)
    assert "job_table" in parsed or any("job" in str(k).lower() for k in parsed.keys())


def test_renderer_output_contains_contact_table():
    renderer = UIRenderer()
    contact = _make_contact()
    output = renderer.render(jobs=[], contacts=[contact], messages=[])
    parsed = json.loads(output)
    assert "contact_table" in parsed or any(
        "contact" in str(k).lower() for k in parsed.keys()
    )


def test_renderer_job_table_has_required_columns():
    renderer = UIRenderer()
    job = _make_job()
    output = renderer.render(jobs=[job], contacts=[], messages=[])
    output_str = output.lower()
    for col in ("role", "company", "source", "score", "apply"):
        assert col in output_str


def test_renderer_output_contains_priority_summary():
    renderer = UIRenderer()
    contact = _make_contact()
    output = renderer.render(jobs=[], contacts=[contact], messages=[])
    parsed = json.loads(output)
    assert "priority_summary" in parsed


def test_renderer_priority_summary_includes_name_and_category():
    renderer = UIRenderer()
    contact = _make_contact()
    output = renderer.render(jobs=[], contacts=[contact], messages=[])
    parsed = json.loads(output)
    summary = parsed["priority_summary"]
    assert len(summary) >= 1
    assert "name" in summary[0]
    assert "category" in summary[0]
