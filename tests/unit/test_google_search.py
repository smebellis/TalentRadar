import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from db.models.job import Job
from search.filters import SearchFilters
from search.google import GoogleJobSearcher


def _make_llm(jobs_list: list) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = json.dumps(jobs_list)
    return mock


def _recent_iso():
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def test_google_searcher_returns_list_of_jobs():
    llm = _make_llm(
        [
            {
                "title": "Engineer",
                "company": "Acme",
                "posted_at": _recent_iso(),
                "apply_url": "https://example.com",
                "raw_description": "Python role",
            }
        ]
    )
    searcher = GoogleJobSearcher(llm=llm)
    results = searcher.search(SearchFilters(keywords=["Python"]))
    assert len(results) == 1
    assert isinstance(results[0], Job)


def test_google_searcher_sets_source_to_google():
    llm = _make_llm(
        [
            {
                "title": "Engineer",
                "company": "Acme",
                "posted_at": _recent_iso(),
                "apply_url": "https://example.com",
                "raw_description": "desc",
            }
        ]
    )
    searcher = GoogleJobSearcher(llm=llm)
    results = searcher.search(SearchFilters())
    assert results[0].source == "google"


def test_google_searcher_filters_out_old_jobs():
    old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    llm = _make_llm(
        [
            {
                "title": "Old Job",
                "company": "Acme",
                "posted_at": old_time,
                "apply_url": "https://example.com",
                "raw_description": "desc",
            }
        ]
    )
    searcher = GoogleJobSearcher(llm=llm)
    results = searcher.search(SearchFilters(time_window_hours=24))
    assert results == []


def test_google_searcher_passes_filters_to_llm():
    llm = _make_llm([])
    searcher = GoogleJobSearcher(llm=llm)
    filters = SearchFilters(keywords=["Python", "Django"], location="Denver, CO")
    searcher.search(filters)
    llm.complete.assert_called_once()
    call_kwargs = llm.complete.call_args.kwargs
    user_payload = json.loads(call_kwargs["user"])
    assert "Python" in user_payload["keywords"]
    assert user_payload["location"] == "Denver, CO"
