import asyncio
import traceback
from pathlib import Path
from typing import Any

from contacts.finder import ContactFinder
from cv.loader import CVLoader
from cv.parser import CVParser
from db.repositories.contact_repo import ContactRepository
from db.repositories.job_repo import JobRepository
from messaging.generator import MessageGenerator
from pipeline.state import PipelineContext, PipelineState
from scoring.contact_scorer import ContactScorer
from scoring.job_scorer import JobScorer
from search.filters import SearchFilters
from search.google import GoogleJobSearcher
from search.linkedin import LinkedInJobSearcher
from ui.renderer import UIRenderer
from utils.logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    def __init__(
        self,
        *,
        cv_loader,
        cv_parser,
        google_searcher,
        linkedin_searcher,
        combiner,
        job_scorer,
        contact_finder,
        contact_scorer,
        message_generator,
        job_repo,
        contact_repo,
        renderer,
        job_threshold: float,
        contact_threshold: float,
        top_n: int,
        progress_callback=None,
    ):
        self._cv_loader = cv_loader
        self._cv_parser = cv_parser
        self._google = google_searcher
        self._linkedin = linkedin_searcher
        self._combiner = combiner
        self._job_scorer = job_scorer
        self._contact_finder = contact_finder
        self._contact_scorer = contact_scorer
        self._msg_gen = message_generator
        self._job_repo = job_repo
        self._contact_repo = contact_repo
        self._renderer = renderer
        self._job_threshold = job_threshold
        self._contact_threshold = contact_threshold
        self._top_n = top_n
        self._progress_callback = progress_callback

    def _fire(self, stage: str, data: dict) -> None:
        if self._progress_callback:
            self._progress_callback(stage, data)

    async def run(self, cv_path: str | Path, filters: SearchFilters) -> PipelineContext:
        ctx = PipelineContext()
        try:
            ctx.state = PipelineState.LOADING_CV
            print("[1/7] Loading and parsing CV...", flush=True)
            self._fire("loading_cv", {})
            raw_cv = self._cv_loader.load(cv_path)
            ctx.resume = self._cv_parser.parse(raw_cv)
            ctx.filters = filters

            ctx.state = PipelineState.SEARCHING
            print("[2/7] Searching Google and LinkedIn...", flush=True)
            self._fire("searching", {})
            google_jobs, linkedin_jobs = await asyncio.gather(
                asyncio.to_thread(self._google.search, filters),
                asyncio.to_thread(self._linkedin.search, filters),
            )
            ctx.jobs = self._combiner(google_jobs, linkedin_jobs)
            print(
                f"  Found {len(ctx.jobs)} jobs (google={len(google_jobs)}, linkedin={len(linkedin_jobs)})",
                flush=True,
            )

            ctx.state = PipelineState.SCORING_JOBS
            print(f"[3/7] Scoring {len(ctx.jobs)} jobs...", flush=True)
            ctx.jobs = self._job_scorer.score(ctx.jobs, ctx.resume)
            top_jobs = [
                j for j in ctx.jobs if (j.fit_score or 0) > self._job_threshold
            ][: self._top_n]
            print(
                f"  {len(top_jobs)} jobs scored above threshold {self._job_threshold}",
                flush=True,
            )
            self._fire("scoring_jobs", {"top_jobs": top_jobs})

            for job in top_jobs:
                await self._job_repo.save(job)

            ctx.state = PipelineState.FINDING_CONTACTS
            print(f"[4/7] Finding contacts for {len(top_jobs)} top jobs...", flush=True)
            self._fire("finding_contacts", {})
            raw_contacts = []
            for job in top_jobs:
                raw_contacts.extend(self._contact_finder.find(job))

            ctx.state = PipelineState.SCORING_CONTACTS
            print(f"[5/7] Scoring {len(raw_contacts)} contacts...", flush=True)
            ctx.contacts = self._contact_scorer.filter_and_sort(
                raw_contacts, searcher_is_veteran=ctx.resume.is_veteran
            )
            self._fire("scoring_contacts", {"contacts": ctx.contacts})

            ctx.state = PipelineState.GENERATE_MESSAGES
            print(f"[6/7] Generating messages for {len(ctx.contacts)} contacts...", flush=True)
            ctx.messages = [
                self._msg_gen.generate(c, j) for c in ctx.contacts for j in top_jobs[:1]
            ]
            self._fire("generating_messages", {"messages": ctx.messages})

            for contact in ctx.contacts:
                await self._contact_repo.save(
                    contact,
                    top_jobs[0].id if top_jobs else None,
                )

            print("[7/7] Rendering output...", flush=True)
            ctx.output = self._renderer.render(
                jobs=top_jobs, contacts=ctx.contacts, messages=ctx.messages
            )

            ctx.state = PipelineState.COMPLETE
            print("Pipeline complete.", flush=True)
            self._fire("complete", {})

        except Exception as exc:
            ctx.errors.append(str(exc))
            ctx.errors.append(traceback.format_exc())
            ctx.state = PipelineState.ERROR
            self._fire("error", {"message": str(exc)})

        return ctx
