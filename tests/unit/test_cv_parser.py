import json
import pytest
from unittest.mock import MagicMock
from cv.parser import CVParser
from db.models.resume import ResumeProfile


def _make_llm(response_dict: dict) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = json.dumps(response_dict)
    return mock


def test_cv_parser_returns_resume_profile():
    llm = _make_llm(
        {
            "skills": ["Python"],
            "experience_years": 3,
            "seniority": "mid",
            "location": "Denver, CO",
            "is_veteran": False,
            "summary": "A developer",
        }
    )
    parser = CVParser(llm=llm)
    result = parser.parse("raw resume text")
    assert isinstance(result, ResumeProfile)


def test_cv_parser_calls_llm_with_resume_text():
    llm = _make_llm(
        {
            "skills": [],
            "experience_years": 0,
            "seniority": "junior",
            "location": "Denver",
            "is_veteran": False,
            "summary": "",
        }
    )
    parser = CVParser(llm=llm)
    parser.parse("raw resume text here")
    llm.complete.assert_called_once()
    call_kwargs = llm.complete.call_args.kwargs
    assert "raw resume text here" in call_kwargs["user"]


def test_cv_parser_infers_is_veteran_true_from_llm():
    llm = _make_llm(
        {
            "skills": ["Leadership"],
            "experience_years": 8,
            "seniority": "senior",
            "location": "Denver, CO",
            "is_veteran": True,
            "summary": "Army veteran",
        }
    )
    parser = CVParser(llm=llm)
    result = parser.parse("U.S. Army, Staff Sergeant, 2012-2020")
    assert result.is_veteran is True


def test_cv_parser_infers_is_veteran_false_when_no_signals():
    llm = _make_llm(
        {
            "skills": ["Python"],
            "experience_years": 3,
            "seniority": "mid",
            "location": "Denver, CO",
            "is_veteran": False,
            "summary": "Software engineer",
        }
    )
    parser = CVParser(llm=llm)
    result = parser.parse("Worked at Google for 3 years")
    assert result.is_veteran is False


def test_cv_parser_system_prompt_contains_veteran_signals():
    from cv.parser import SYSTEM_PROMPT

    assert "veteran" in SYSTEM_PROMPT.lower()
    assert "military" in SYSTEM_PROMPT.lower() or "MOS" in SYSTEM_PROMPT
