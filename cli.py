import argparse
import asyncio

from hydra import compose, initialize

from contacts.finder import ContactFinder
from cv.loader import CVLoader
from cv.parser import CVParser
from db.connection import create_pool
from db.repositories.contact_repo import ContactRepository
from db.repositories.job_repo import JobRepository
from llm.claude import ClaudeClient
from messaging.generator import MessageGenerator
from pipeline.combiner import combine_jobs
from pipeline.orchestrator import Orchestrator
from scoring.contact_scorer import ContactScorer
from scoring.job_scorer import JobScorer
from search.filters import SearchFilters
from search.google import GoogleJobSearcher
from search.linkedin import LinkedInJobSearcher
from ui.renderer import UIRenderer
from utils.logger import get_logger

logger = get_logger(__name__)


def build_orchestrator(cfg) -> Orchestrator:
    llm = ClaudeClient(api_key=cfg.anthropic_api_key)
    return Orchestrator(
        cv_loader=CVLoader(),
        cv_parser=CVParser(llm=llm),
        google_searcher=GoogleJobSearcher(llm=llm),
        linkedin_searcher=LinkedInJobSearcher(api_token=cfg.apify_api_token),
        combiner=combine_jobs,
        job_scorer=JobScorer(llm=llm),
        contact_finder=ContactFinder(
            apify_client=None,
            vibe_client=None,
            max_per_category=cfg.scoring.max_contacts_per_category,
        ),
        contact_scorer=ContactScorer(
            threshold=cfg.scoring.contact_score_threshold,
            veteran_boost=cfg.scoring.veteran_score_boost,
        ),
        message_generator=MessageGenerator(llm=llm),
        job_repo=None,
        contact_repo=None,
        renderer=UIRenderer(),
        job_threshold=cfg.scoring.job_score_threshold,
        contact_threshold=cfg.scoring.contact_score_threshold,
        top_n=cfg.scoring.top_n_jobs,
    )


async def run_full(cfg, cv_path: str, keywords: list[str]):
    pool = await create_pool(
        host=cfg.database.host,
        port=int(cfg.database.port),
        db=cfg.database.db,
        user=cfg.database.user,
        password=cfg.database.password,
    )
    llm = ClaudeClient(api_key=cfg.anthropic_api_key)
    orch = Orchestrator(
        cv_loader=CVLoader(),
        cv_parser=CVParser(llm=llm),
        google_searcher=GoogleJobSearcher(llm=llm),
        linkedin_searcher=LinkedInJobSearcher(api_token=cfg.apify_api_token),
        combiner=combine_jobs,
        job_scorer=JobScorer(llm=llm),
        contact_finder=ContactFinder(
            apify_client=None,
            vibe_client=None,
            max_per_category=cfg.scoring.max_contacts_per_category,
        ),
        contact_scorer=ContactScorer(
            threshold=cfg.scoring.contact_score_threshold,
            veteran_boost=cfg.scoring.veteran_score_boost,
        ),
        message_generator=MessageGenerator(llm=llm),
        job_repo=JobRepository(pool=pool),
        contact_repo=ContactRepository(pool=pool),
        renderer=UIRenderer(),
        job_threshold=cfg.scoring.job_score_threshold,
        contact_threshold=cfg.scoring.contact_score_threshold,
        top_n=cfg.scoring.top_n_jobs,
    )
    filters = SearchFilters(
        keywords=keywords or cfg.search.keywords,
        location=cfg.search.location,
        remote=cfg.search.remote,
        onsite=cfg.search.onsite,
        job_type=cfg.search.job_type,
        time_window_hours=cfg.search.time_window_hours,
    )
    await orch.run(cv_path=cv_path, filters=filters)
    await pool.close()


def main():
    parser = argparse.ArgumentParser(description="Job Search Agent")
    parser.add_argument(
        "mode", choices=["search", "full", "contacts-only"], help="Pipeline mode"
    )
    parser.add_argument("--cv", required=True, help="Path to resume PDF")
    parser.add_argument("--keywords", nargs="*", default=[], help="Search keywords")
    args = parser.parse_args()

    with initialize(config_path="config", version_base=None):
        cfg = compose(config_name="config")

    if args.mode == "full":
        asyncio.run(run_full(cfg, cv_path=args.cv, keywords=args.keywords))
    else:
        logger.info(f"Mode '{args.mode}' not yet implemented — use 'full'")


if __name__ == "__main__":
    main()
