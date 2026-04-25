import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from db.models.job import Job
from db.models.resume import ResumeProfile
from scoring.job_scorer import JobScorer


def _make_resume():
    return ResumeProfile(
        skills=["Python", "SQL"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Experienced engineer",
    )


def _make_job(title="Engineer", company="Acme"):
    return Job(
        title=title,
        company=company,
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="Python developer needed",
    )


def _make_llm(score: float) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = json.dumps({"score": score, "reason": "Good fit"})
    return mock


def test_job_scorer_sets_fit_score_on_each_job():
    llm = _make_llm(8.0)
    scorer = JobScorer(llm=llm)
    jobs = [_make_job()]
    result = scorer.score(jobs, _make_resume())
    assert result[0].fit_score == 8.0


def test_job_scorer_score_is_between_0_and_10():
    llm = _make_llm(9.5)
    scorer = JobScorer(llm=llm)
    result = scorer.score([_make_job()], _make_resume())
    assert 0.0 <= result[0].fit_score <= 10.0


def test_job_scorer_calls_llm_once_per_job():
    llm = _make_llm(7.0)
    scorer = JobScorer(llm=llm)
    jobs = [_make_job("Job A"), _make_job("Job B"), _make_job("Job C")]
    scorer.score(jobs, _make_resume())
    assert llm.complete.call_count == 3


def test_job_scorer_passes_resume_skills_to_llm():
    llm = _make_llm(7.5)
    scorer = JobScorer(llm=llm)
    resume = _make_resume()
    scorer.score([_make_job()], resume)
    call_kwargs = llm.complete.call_args.kwargs
    assert "Python" in call_kwargs["user"]


def test_job_scorer_sorts_by_score_descending():
    scores = [6.0, 9.0, 7.5]
    call_count = [0]

    def fake_complete(**kwargs):
        score = scores[call_count[0]]
        call_count[0] += 1
        return json.dumps({"score": score, "reason": ""})

    llm = MagicMock()
    llm.complete.side_effect = fake_complete
    scorer = JobScorer(llm=llm)
    result = scorer.score(
        [_make_job("A"), _make_job("B"), _make_job("C")], _make_resume()
    )
    assert result[0].fit_score == 9.0
    assert result[-1].fit_score == 6.0
