import pytest

from db.models.contact import Contact
from scoring.contact_scorer import ContactScorer


def _make_contact(category="hiring_manager", is_veteran=False, score=4.0):
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
    # hiring_manager scores 4 (5-1), both pass threshold=1
    scorer = ContactScorer(threshold=1, veteran_boost=1)
    contacts = [_make_contact(score=0), _make_contact(score=0)]
    result = scorer.filter_and_sort(contacts, searcher_is_veteran=False)
    assert len(result) == 2
    assert result[0].relevance_score == 4


def test_contact_scorer_applies_veteran_boost_when_searcher_is_veteran():
    # veteran scores 5-3=2, plus boost of 1.5 = 3.5
    scorer = ContactScorer(threshold=1.0, veteran_boost=1.5)
    vet_contact = _make_contact(category="veteran", is_veteran=True, score=0)
    result = scorer.filter_and_sort([vet_contact], searcher_is_veteran=True)
    assert len(result) == 1
    assert result[0].relevance_score == pytest.approx(3.5)


def test_contact_scorer_no_boost_when_searcher_is_not_veteran():
    # veteran scores 5-3=2, no boost applied
    scorer = ContactScorer(threshold=1.0, veteran_boost=1.5)
    vet_contact = _make_contact(category="veteran", is_veteran=True, score=0)
    result = scorer.filter_and_sort([vet_contact], searcher_is_veteran=False)
    assert len(result) == 1
    assert result[0].relevance_score == 2


def test_contact_scorer_sorts_veterans_first_when_searcher_is_veteran():
    scorer = ContactScorer(threshold=1.0, veteran_boost=1.5)
    peer = _make_contact(category="peer", is_veteran=False, score=9.0)
    vet = _make_contact(category="veteran", is_veteran=True, score=1.0)
    result = scorer.filter_and_sort([peer, vet], searcher_is_veteran=True)
    assert result[0].category == "veteran"


def test_contact_scorer_standard_order_when_not_veteran():
    scorer = ContactScorer(threshold=1.0, veteran_boost=1.5)
    recruiter = _make_contact(category="recruiter", score=9.0)
    hiring_manager = _make_contact(category="hiring_manager", score=8.0)
    peer = _make_contact(category="peer", score=7.5)
    result = scorer.filter_and_sort(
        [recruiter, peer, hiring_manager], searcher_is_veteran=False
    )
    assert result[0].category == "hiring_manager"
