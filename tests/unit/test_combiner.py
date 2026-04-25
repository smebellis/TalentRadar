import pytest
from datetime import datetime, timezone
from db.models.job import Job
from pipeline.combiner import combine_jobs


def _make_job(title, company, source="google"):
    return Job(
        title=title,
        company=company,
        posted_at=datetime.now(timezone.utc),
        source=source,
        apply_url="https://example.com",
        raw_description="desc",
    )


def test_combine_jobs_merges_two_lists():
    google_jobs = [_make_job("Engineer", "Acme", "google")]
    linkedin_jobs = [_make_job("Analyst", "BetaCo", "linkedin")]
    result = combine_jobs(google_jobs, linkedin_jobs)
    assert len(result) == 2


def test_combine_jobs_deduplicates_by_title_and_company():
    job_a = _make_job("Engineer", "Acme", "google")
    job_b = _make_job("Engineer", "Acme", "linkedin")
    result = combine_jobs([job_a], [job_b])
    assert len(result) == 1


def test_combine_jobs_keeps_google_version_on_duplicate():
    job_a = _make_job("Engineer", "Acme", "google")
    job_b = _make_job("Engineer", "Acme", "linkedin")
    result = combine_jobs([job_a], [job_b])
    assert result[0].source == "google"


def test_combine_jobs_handles_empty_lists():
    result = combine_jobs([], [])
    assert result == []


def test_combine_jobs_preserves_unique_jobs_from_both_sources():
    google_jobs = [_make_job("Engineer", "Acme"), _make_job("Analyst", "BetaCo")]
    linkedin_jobs = [_make_job("Engineer", "Acme"), _make_job("Designer", "GammaCo")]
    result = combine_jobs(google_jobs, linkedin_jobs)
    companies = {j.company for j in result}
    assert companies == {"Acme", "BetaCo", "GammaCo"}
