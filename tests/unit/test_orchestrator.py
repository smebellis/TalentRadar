from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.models.resume import ResumeProfile
from pipeline.orchestrator import Orchestrator
from pipeline.state import PipelineContext, PipelineState
from search.filters import SearchFilters


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
        renderer=MagicMock(),
        job_threshold=7.0,
        contact_threshold=7.0,
        top_n=10,
    )

    import asyncio

    ctx = asyncio.run(orch.run(cv_path="missing.pdf", filters=_make_filters()))
    assert ctx.state == PipelineState.ERROR
    assert len(ctx.errors) > 0
