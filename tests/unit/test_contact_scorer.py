import pytest

from db.models.contact import Contact
from scoring.contact_scorer import ContactScorer


def _make_contact(category="hiring_manager", is_veteran=False, score=7.5):
    return Contact(
        name="Test Person",
        title="Manager",
        company="Acme",
        category=category,
        linkedin_url="https://linkedin.com/in/test",
        relevance_score=score,
        is_veteran=is_veteran,
        notes="",
    )


def test_contact_scorer_filters_below_threshold():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    contacts = [_make_contact(score=6.5), _make_contact(score=8.0)]
    result = scorer.filter_and_sort(contacts, searcher_is_veteran=False)
    assert len(result) == 1
    assert result[0].relevance_score == 8.0


def test_contact_scorer_applies_veteran_boost_when_searcher_is_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    vet_contact = _make_contact(category="veteran", is_veteran=True, score=6.0)
    result = scorer.filter_and_sort([vet_contact], searcher_is_veteran=True)
    assert len(result) == 1
    assert result[0].relevance_score == pytest.approx(7.5)


def test_contact_scorer_no_boost_when_searcher_is_not_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    vet_contact = _make_contact(category="veteran", is_veteran=True, score=6.0)
    result = scorer.filter_and_sort([vet_contact], searcher_is_veteran=False)
    assert result == []


def test_contact_scorer_sorts_veterans_first_when_searcher_is_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    peer = _make_contact(category="peer", is_veteran=False, score=9.0)
    vet = _make_contact(category="veteran", is_veteran=True, score=7.0)
    result = scorer.filter_and_sort([peer, vet], searcher_is_veteran=True)
    assert result[0].category == "veteran"


def test_contact_scorer_standard_order_when_not_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    recruiter = _make_contact(category="recruiter", score=9.0)
    hiring_manager = _make_contact(category="hiring_manager", score=8.0)
    peer = _make_contact(category="peer", score=7.5)
    result = scorer.filter_and_sort(
        [recruiter, peer, hiring_manager], searcher_is_veteran=False
    )
    assert result[0].category == "hiring_manager"
