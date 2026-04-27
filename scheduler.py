import asyncio
import time

from cli import run_full
from utils.logger import get_logger

logger = get_logger(__name__)


def run_on_schedule(interval_seconds: int, cv_path: str, keywords: list[str], cfg):
    logger.info(f"Scheduler started — running every {interval_seconds}s")
    while True:
        logger.info("Scheduler: starting pipeline run")
        asyncio.run(run_full(cfg=cfg, cv_path=cv_path, keywords=keywords))
        logger.info(f"Scheduler: run complete — sleeping {interval_seconds}s")
        time.sleep(interval_seconds)
