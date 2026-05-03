import json
import logging
import os
from urllib.parse import quote_plus

import httpx
from apify_client import ApifyClient

logger = logging.getLogger(__name__)


class ApifyContactClient:
    """Find people on LinkedIn using a dedicated people-search actor.

    Requires a LinkedIn session cookie exported via the Cookie-Editor
    Chrome extension and passed in the ``LINKEDIN_COOKIES`` environment
    variable as a JSON string.  When the cookie is absent the method returns
    an empty list so the rest of the pipeline degrades gracefully.
    """

    def __init__(self, api_token: str, actor_id: str | None = None) -> None:
        self.client = ApifyClient(api_token)
        self.actor_id = actor_id or os.getenv(
            "APIFY_CONTACT_ACTOR_ID", "curious_coder/linkedin-people-search-scraper"
        )

    def find_people(self, company: str, job_title: str) -> list[dict]:
        cookie_raw = os.getenv("LINKEDIN_COOKIES")
        if not cookie_raw:
            return []

        try:
            cookie = json.loads(cookie_raw)
        except json.JSONDecodeError:
            return []

        keywords = quote_plus(f"{job_title} recruiter")
        company_encoded = quote_plus(company)
        search_url = (
            "https://www.linkedin.com/search/results/people/"
            f"?keywords={keywords}&company={company_encoded}"
        )

        run = self.client.actor(self.actor_id).call(
            run_input={
                "searchUrl": search_url,
                "cookie": cookie,
                "startPage": 1,
                "endPage": 1,
            }
        )
        dataset = self.client.dataset(run["defaultDatasetId"])
        items = list(dataset.iterate_items())

        prospects: list[dict] = []
        seen_urls: set[str] = set()
        for item in items:
            linkedin_url = item.get("profileUrl") or ""
            if not linkedin_url or linkedin_url in seen_urls:
                continue
            seen_urls.add(linkedin_url)
            prospects.append(
                {
                    "name": item.get("fullName") or "",
                    "title": item.get("headline") or "",
                    "linkedin_url": linkedin_url,
                    "company": company,
                    "email": None,
                    "notes": item.get("location") or "",
                }
            )

        return prospects


class VibeProspectingClient:
    def __init__(self, api_key: str | None, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.base_url = base_url or os.getenv("VIBE_API_BASE_URL")

    def enrich(self, people: list[dict]) -> list[dict]:
        if not people or not self.api_key or not self.base_url:
            return people

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    f"{self.base_url.rstrip('/')}/enrich",
                    headers={"api_key": self.api_key},
                    json={"people": people},
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return people

        enriched = data.get("people") if isinstance(data, dict) else None
        return enriched if isinstance(enriched, list) else people

    def find_people(self, company: str, job_title: str, max_results: int = 20) -> list[dict]:
        if not self.base_url or not self.api_key:
            logger.warning("VibeProspectingClient: base_url or api_key not configured")
            return []

        headers = {
            "api_key": self.api_key,
            "Content-Type": "application/json",
        }
        base = self.base_url.rstrip("/")

        try:
            with httpx.Client(timeout=30.0) as client:
                # Step 1: resolve company name → business_id
                match_resp = client.post(
                    f"{base}/businesses/match",
                    headers=headers,
                    json={"businesses_to_match": [{"name": company}]},
                )
                if match_resp.status_code == 402:
                    logger.warning("VibeProspectingClient: credits exhausted (match)")
                    return []
                if match_resp.status_code == 403:
                    raise RuntimeError(
                        "Vibe API 403 Forbidden — REST API key not authorized. "
                        "Generate a REST key at explorium.ai and set VIBE_API_KEY in .env"
                    )
                match_resp.raise_for_status()
                matches = match_resp.json().get("matched_businesses") or []
                if not matches:
                    logger.warning("VibeProspectingClient: no match for company %r", company)
                    return []
                business_id = matches[0]["business_id"]

                # Step 2: fetch prospects for that business
                fetch_resp = client.post(
                    f"{base}/prospects",
                    headers=headers,
                    json={
                        "filters": {"business_id": {"values": [business_id]}},
                        "page_size": max_results,
                    },
                )
                if fetch_resp.status_code == 402:
                    logger.warning("VibeProspectingClient: credits exhausted (fetch)")
                    return []
                fetch_resp.raise_for_status()
                data = fetch_resp.json()
        except RuntimeError:
            raise
        except Exception as exc:
            logger.warning("VibeProspectingClient.find_people failed: %s", exc, exc_info=True)
            return []

        logger.debug("VibeProspectingClient raw response keys: %s", list(data.keys()))
        raw_people = (
            (data.get("preview") or {}).get("preview_data")
            or data.get("prospects")
            or data.get("data")
            or []
        )
        logger.info("VibeProspectingClient: %d raw people for %r", len(raw_people), company)

        prospects: list[dict] = []
        for p in raw_people:
            name = p.get("full_name") or ""
            title = p.get("job_title") or ""
            url_array = p.get("linkedin_url_array")
            linkedin = (
                p.get("linkedin")
                or (url_array[0] if isinstance(url_array, list) and url_array else None)
                or ""
            )
            if linkedin and not linkedin.startswith("http"):
                linkedin = "https://" + linkedin
            city = p.get("city") or ""
            region = p.get("region_name") or ""
            notes = ", ".join(filter(None, [city, region]))[:100]
            prospects.append(
                {
                    "name": name,
                    "title": title,
                    "company": company,
                    "linkedin_url": linkedin,
                    "email": None,
                    "notes": notes,
                }
            )

        return prospects
