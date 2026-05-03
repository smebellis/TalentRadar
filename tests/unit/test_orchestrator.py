from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.models.contact import Contact
from db.models.job import Job
from db.models.resume import ResumeProfile
from pipeline.combiner import combine_jobs
from pipeline.orchestrator import Orchestrator
from pipeline.state import PipelineContext, PipelineState
from search.filters import SearchFilters


def _make_job(score: float = 8.0) -> Job:
    return Job(
        title="Software Engineer",
        company="Acme Corp",
        posted_at=datetime(2026, 1, 1),
        source="google",
        apply_url="https://example.com/apply",
        raw_description="Python engineer role",
        fit_score=score,
    )


def _make_contact() -> Contact:
    return Contact(
        name="Jane Doe",
        title="Engineering Manager",
        company="Acme Corp",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/janedoe",
        relevance_score=8.0,
        notes="Referred by pipeline",
    )


def _make_resume():
    return ResumeProfile(
        skills=["Python"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Engineer",
    )


def _make_filters():
    return SearchFilters(keywords=["Python"], location="Denver, CO")


def test_orchestrator_sets_state_to_complete_on_success():
    mock_cv_loader = MagicMock()
    mock_cv_parser = MagicMock()
    mock_cv_parser.parse.return_value = _make_resume()
    mock_google = MagicMock()
    mock_google.search.return_value = []
    mock_linkedin = MagicMock()
    mock_linkedin.search.return_value = []
    mock_scorer = MagicMock()
    mock_scorer.score.return_value = []
    mock_contact_finder = MagicMock()
    mock_contact_scorer = MagicMock()
    mock_contact_scorer.filter_and_sort.return_value = []
    mock_msg_gen = MagicMock()
    mock_job_repo = AsyncMock()
    mock_contact_repo = AsyncMock()
    mock_renderer = MagicMock()
    mock_renderer.render.return_value = '{"job_table": []}'

    orch = Orchestrator(
        cv_loader=mock_cv_loader,
        cv_parser=mock_cv_parser,
        google_searcher=mock_google,
        linkedin_searcher=mock_linkedin,
        combiner=MagicMock(return_value=[]),
        job_scorer=mock_scorer,
        contact_finder=mock_contact_finder,
        contact_scorer=mock_contact_scorer,
        message_generator=mock_msg_gen,
        job_repo=mock_job_repo,
        contact_repo=mock_contact_repo,
        message_repo=AsyncMock(),
        renderer=mock_renderer,
        job_threshold=7.0,
        contact_threshold=7.0,
        top_n=10,
    )

    import asyncio

    ctx = asyncio.run(orch.run(cv_path="resume.pdf", filters=_make_filters()))
    assert ctx.state == PipelineState.COMPLETE


def test_orchestrator_sets_error_state_on_exception(caplog):
    mock_cv_loader = MagicMock()
    mock_cv_loader.load.side_effect = FileNotFoundError("resume.pdf not found")
    mock_cv_parser = MagicMock()

    orch = Orchestrator(
        cv_loader=mock_cv_loader,
        cv_parser=mock_cv_parser,
        google_searcher=MagicMock(),
        linkedin_searcher=MagicMock(),
        combiner=MagicMock(return_value=[]),
        job_scorer=MagicMock(),
        contact_finder=MagicMock(),
        contact_scorer=MagicMock(),
        message_generator=MagicMock(),
        job_repo=AsyncMock(),
        contact_repo=AsyncMock(),
        message_repo=AsyncMock(),
        renderer=MagicMock(),
        job_threshold=7.0,
        contact_threshold=7.0,
        top_n=10,
    )

    import asyncio

    ctx = asyncio.run(orch.run(cv_path="missing.pdf", filters=_make_filters()))
    assert ctx.state == PipelineState.ERROR
    assert len(ctx.errors) > 0


@pytest.mark.asyncio
async def test_orchestrator_fires_progress_callback_at_each_stage():
    """Callback is called for each pipeline stage with the stage name."""
    fired_stages = []

    def callback(stage, data):
        fired_stages.append(stage)

    job = _make_job(score=8.0)
    contact = _make_contact()

    cv_loader = MagicMock()
    cv_loader.load.return_value = "raw cv text"
    cv_parser = MagicMock()
    cv_parser.parse.return_value = MagicMock(is_veteran=False)
    google = MagicMock()
    google.search.return_value = [job]
    linkedin = MagicMock()
    linkedin.search.return_value = []
    job_scorer = MagicMock()
    job_scorer.score.return_value = [job]
    contact_finder = MagicMock()
    contact_finder.find.return_value = [contact]
    contact_scorer = MagicMock()
    contact_scorer.filter_and_sort.return_value = [contact]
    msg_gen = MagicMock()
    msg_gen.generate.return_value = "Hi there"
    job_repo = AsyncMock()
    contact_repo = AsyncMock()
    renderer = MagicMock()
    renderer.render.return_value = '{"output": "test"}'

    orch = Orchestrator(
        cv_loader=cv_loader,
        cv_parser=cv_parser,
        google_searcher=google,
        linkedin_searcher=linkedin,
        combiner=combine_jobs,
        job_scorer=job_scorer,
        contact_finder=contact_finder,
        contact_scorer=contact_scorer,
        message_generator=msg_gen,
        job_repo=job_repo,
        contact_repo=contact_repo,
        message_repo=AsyncMock(),
        renderer=renderer,
        job_threshold=5.0,
        contact_threshold=5.0,
        top_n=5,
        progress_callback=callback,
    )
    filters = SearchFilters(
        keywords=["python"],
        location="Denver",
        remote=True,
        onsite=False,
        job_type="full_time",
        time_window_hours=48,
    )
    ctx = await orch.run(cv_path="resume.pdf", filters=filters)

    assert "loading_cv" in fired_stages
    assert "searching" in fired_stages
    assert "scoring_jobs" in fired_stages
    assert "finding_contacts" in fired_stages
    assert "scoring_contacts" in fired_stages
    assert "generating_messages" in fired_stages
    assert "complete" in fired_stages


@pytest.mark.asyncio
async def test_orchestrator_callback_receives_jobs_at_scoring_stage():
    received = {}

    def callback(stage, data):
        received[stage] = data

    job = _make_job(score=8.0)
    contact = _make_contact()

    cv_loader = MagicMock()
    cv_loader.load.return_value = "raw cv text"
    cv_parser = MagicMock()
    cv_parser.parse.return_value = MagicMock(is_veteran=False)
    google = MagicMock()
    google.search.return_value = [job]
    linkedin = MagicMock()
    linkedin.search.return_value = []
    job_scorer = MagicMock()
    job_scorer.score.return_value = [job]
    contact_finder = MagicMock()
    contact_finder.find.return_value = [contact]
    contact_scorer = MagicMock()
    contact_scorer.filter_and_sort.return_value = [contact]
    msg_gen = MagicMock()
    msg_gen.generate.return_value = "Hi there"
    job_repo = AsyncMock()
    contact_repo = AsyncMock()
    renderer = MagicMock()
    renderer.render.return_value = '{"output": "test"}'

    orch = Orchestrator(
        cv_loader=cv_loader,
        cv_parser=cv_parser,
        google_searcher=google,
        linkedin_searcher=linkedin,
        combiner=combine_jobs,
        job_scorer=job_scorer,
        contact_finder=contact_finder,
        contact_scorer=contact_scorer,
        message_generator=msg_gen,
        job_repo=job_repo,
        contact_repo=contact_repo,
        message_repo=AsyncMock(),
        renderer=renderer,
        job_threshold=5.0,
        contact_threshold=5.0,
        top_n=5,
        progress_callback=callback,
    )
    filters = SearchFilters(
        keywords=["python"],
        location="Denver",
        remote=True,
        onsite=False,
        job_type="full_time",
        time_window_hours=48,
    )
    await orch.run(cv_path="resume.pdf", filters=filters)

    assert "top_jobs" in received.get("scoring_jobs", {})
    assert "contacts" in received.get("scoring_contacts", {})
    assert "messages" in received.get("generating_messages", {})
