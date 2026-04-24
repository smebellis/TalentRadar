import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from search.linkedin import LinkedInJobSearcher
from search.filters import SearchFilters
from db.models.job import Job


def _recent_iso():
    return (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()


def test_linkedin_searcher_returns_list_of_jobs():
    mock_item = {
        "title": "Data Engineer",
        "companyName": "TechCorp",
        "postedAt": _recent_iso(),
        "jobUrl": "https://linkedin.com/jobs/123",
        "description": "Build pipelines",
    }
    with patch("search.linkedin.ApifyClient") as MockApify:
        mock_run = {"defaultDatasetId": "dataset-123"}
        MockApify.return_value.actor.return_value.call.return_value = mock_run
        MockApify.return_value.dataset.return_value.iterate_items.return_value = iter([mock_item])

        searcher = LinkedInJobSearcher(api_token="test-token")
        results = searcher.search(SearchFilters(keywords=["Python"]))

    assert len(results) == 1
    assert isinstance(results[0], Job)


def test_linkedin_searcher_sets_source_to_linkedin():
    mock_item = {
        "title": "Engineer", "companyName": "Corp",
        "postedAt": _recent_iso(),
        "jobUrl": "https://linkedin.com/jobs/1",
        "description": "desc",
    }
    with patch("search.linkedin.ApifyClient") as MockApify:
        mock_run = {"defaultDatasetId": "ds1"}
        MockApify.return_value.actor.return_value.call.return_value = mock_run
        MockApify.return_value.dataset.return_value.iterate_items.return_value = iter([mock_item])

        searcher = LinkedInJobSearcher(api_token="token")
        results = searcher.search(SearchFilters())

    assert results[0].source == "linkedin"


def test_linkedin_searcher_filters_old_jobs():
    old_item = {
        "title": "Old Job", "companyName": "OldCo",
        "postedAt": (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(),
        "jobUrl": "https://linkedin.com/jobs/2",
        "description": "old",
    }
    with patch("search.linkedin.ApifyClient") as MockApify:
        mock_run = {"defaultDatasetId": "ds2"}
        MockApify.return_value.actor.return_value.call.return_value = mock_run
        MockApify.return_value.dataset.return_value.iterate_items.return_value = iter([old_item])

        searcher = LinkedInJobSearcher(api_token="token")
        results = searcher.search(SearchFilters(time_window_hours=24))

    assert results == []