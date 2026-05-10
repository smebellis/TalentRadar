from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from db.models.job import Job
from search.filters import SearchFilters
from search.linkedin import LinkedInJobSearcher


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

    mock_client = MagicMock()
    mock_run = {"defaultDatasetId": "dataset-123"}
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter([mock_item])

    searcher = LinkedInJobSearcher(mock_client, actor_id="test-123")
    results = searcher.search(SearchFilters(keywords=["Python"]))

    assert len(results) == 1
    assert isinstance(results[0], Job)


def test_linkedin_searcher_sets_source_to_linkedin():
    mock_item = {
        "title": "Engineer",
        "companyName": "Corp",
        "postedAt": _recent_iso(),
        "jobUrl": "https://linkedin.com/jobs/1",
        "description": "desc",
    }
    mock_client = MagicMock()
    mock_run = {"defaultDatasetId": "dataset-123"}
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter([mock_item])

    searcher = LinkedInJobSearcher(mock_client, actor_id="test-123")

    results = searcher.search(SearchFilters())

    assert results[0].source == "linkedin"


def test_linkedin_searcher_filters_old_jobs():
    old_item = {
        "title": "Old Job",
        "companyName": "OldCo",
        "postedAt": (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(),
        "jobUrl": "https://linkedin.com/jobs/2",
        "description": "old",
    }
    mock_client = MagicMock()
    mock_run = {"defaultDatasetId": "dataset-123"}
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter([old_item])

    searcher = LinkedInJobSearcher(mock_client, actor_id="test-123")
    results = searcher.search(SearchFilters(time_window_hours=24))

    assert results == []


def test_linkedin_searcher_custom_actor_id() -> None:
    mock_item = {
        "title": "Engineer",
        "companyName": "Corp",
        "postedAt": _recent_iso(),
        "jobUrl": "https://linkedin.com/jobs/1",
        "description": "desc",
    }
    mock_client = MagicMock()
    mock_run = {"defaultDatasetId": "dataset-123"}
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter([mock_item])

    searcher = LinkedInJobSearcher(mock_client, actor_id="test-123")
    results = searcher.search(SearchFilters(time_window_hours=24))

    mock_client.actor.assert_called_with("test-123")
