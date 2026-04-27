"""
Integration tests — hit real APIs. Run manually only:
    pytest tests/integration/ -v

Requires all environment variables to be set (see .env.example).
DO NOT run in CI.
"""

import asyncio
import os
from pathlib import Path

import pytest


@pytest.mark.integration
def test_full_pipeline_runs_end_to_end():
    """Run the full pipeline with real APIs against a sample resume."""
    pytest.skip("Run manually: set env vars and provide a real resume PDF")


@pytest.mark.integration
def test_google_search_returns_jobs():
    pytest.skip("Run manually: requires ANTHROPIC_API_KEY")


@pytest.mark.integration
def test_linkedin_search_returns_jobs():
    pytest.skip("Run manually: requires APIFY_API_TOKEN")
