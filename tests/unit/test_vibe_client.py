import os
from unittest.mock import MagicMock, patch

import pytest

from contacts.clients import VibeProspectingClient


def _make_client():
    return VibeProspectingClient(
        api_key="test-key", base_url="https://api.explorium.ai/v1"
    )


def _mock_match_response(business_id="abc123"):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "matched_businesses": [{"business_id": business_id}]
    }
    resp.raise_for_status = MagicMock()
    return resp


def _mock_fetch_response(people):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "preview": {"preview_data": people}
    }
    resp.raise_for_status = MagicMock()
    return resp


def test_find_people_maps_response_correctly():
    client = _make_client()
    raw_person = {
        "prospect_full_name": "Jane Smith",
        "prospect_job_title": "Engineering Manager",
        "prospect_linkedin": "linkedin.com/in/janesmith",
        "prospect_company_name": "Acme Corp",
        "prospect_city": "denver",
        "prospect_region_name": "colorado",
    }
    match_resp = _mock_match_response("biz-1")
    fetch_resp = _mock_fetch_response([raw_person])

    with patch("contacts.clients.httpx.Client") as mock_cls:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__.return_value = mock_http
        mock_http.post.side_effect = [match_resp, fetch_resp]

        result = client.find_people("Acme Corp", "Engineer")

    assert len(result) == 1
    p = result[0]
    assert p["name"] == "Jane Smith"
    assert p["title"] == "Engineering Manager"
    assert p["linkedin_url"] == "https://linkedin.com/in/janesmith"
    assert p["company"] == "Acme Corp"
    assert p["email"] is None
    assert "denver" in p["notes"]


def test_find_people_returns_empty_when_base_url_unset():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("VIBE_API_BASE_URL", None)
        client = VibeProspectingClient(api_key="test-key", base_url=None)
    result = client.find_people("Acme Corp", "Engineer")
    assert result == []


def test_find_people_returns_empty_when_api_key_unset():
    client = VibeProspectingClient(api_key=None, base_url="https://api.explorium.ai/v1")
    result = client.find_people("Acme Corp", "Engineer")
    assert result == []


def test_find_people_returns_empty_on_http_error():
    client = _make_client()

    with patch("contacts.clients.httpx.Client") as mock_cls:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__.return_value = mock_http
        mock_http.post.side_effect = Exception("connection error")

        result = client.find_people("Acme Corp", "Engineer")

    assert result == []


def test_find_people_returns_empty_on_402():
    client = _make_client()
    resp_402 = MagicMock()
    resp_402.status_code = 402
    resp_402.raise_for_status = MagicMock()
    resp_402.json.return_value = {}

    with patch("contacts.clients.httpx.Client") as mock_cls:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__.return_value = mock_http
        mock_http.post.return_value = resp_402

        result = client.find_people("Acme Corp", "Engineer")

    assert result == []


def test_find_people_returns_empty_when_no_business_match():
    client = _make_client()
    no_match_resp = MagicMock()
    no_match_resp.status_code = 200
    no_match_resp.json.return_value = {"matched_businesses": []}
    no_match_resp.raise_for_status = MagicMock()

    with patch("contacts.clients.httpx.Client") as mock_cls:
        mock_http = MagicMock()
        mock_cls.return_value.__enter__.return_value = mock_http
        mock_http.post.return_value = no_match_resp

        result = client.find_people("Unknown Corp", "Engineer")

    assert result == []
