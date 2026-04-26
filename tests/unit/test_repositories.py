import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.models.contact import Contact
from db.models.job import Job
from db.repositories.contact_repo import ContactRepository
from db.repositories.job_repo import JobRepository


def _make_job():
    return Job(
        title="Engineer",
        company="Acme",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
        fit_score=8.5,
    )


def _make_contact():
    return Contact(
        name="Jane",
        title="Manager",
        company="Acme",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.0,
        is_veteran=False,
        notes="",
    )


@pytest.mark.asyncio
async def test_job_repository_save_executes_insert():
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    repo = JobRepository(pool=mock_pool)
    await repo.save(_make_job())
    mock_conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_contact_repository_save_executes_insert():
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    repo = ContactRepository(pool=mock_pool)
    await repo.save(_make_contact(), job_id=_make_job().id)
    mock_conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_job_repository_get_all_returns_list():
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    repo = JobRepository(pool=mock_pool)
    result = await repo.get_all()
    assert isinstance(result, list)
