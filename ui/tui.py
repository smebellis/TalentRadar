from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer

from ui.widgets.contacts_table import ContactsTable
from ui.widgets.jobs_table import JobsTable
from ui.widgets.messages_panel import MessagesPanel
from ui.widgets.progress_panel import ProgressPanel


class JobSearchApp(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-rows: 5 1fr 1fr 1;
    }
    ProgressPanel {
        column-span: 2;
        border: solid $accent;
        padding: 0 1;
    }
    JobsTable {
        border: solid $primary;
    }
    ContactsTable {
        border: solid $primary;
    }
    MessagesPanel {
        column-span: 2;
        border: solid $secondary;
    }
    Footer {
        column-span: 2;
    }
    """

    BINDINGS = [Binding("q", "quit", "Quit")]

    def __init__(self, cfg, cv_path: str, keywords: list, _skip_pipeline: bool = False):
        super().__init__()
        self._cfg = cfg
        self._cv_path = cv_path
        self._keywords = keywords
        self._skip_pipeline = _skip_pipeline

    def compose(self) -> ComposeResult:
        yield ProgressPanel(id="progress")
        yield JobsTable(id="jobs")
        yield ContactsTable(id="contacts")
        yield MessagesPanel(id="messages")
        yield Footer()

    def on_mount(self) -> None:
        if not self._skip_pipeline:
            self.run_worker(self._run_pipeline, exclusive=True)

    def _progress_callback(self, stage: str, data: dict) -> None:
        if stage == "loading_cv":
            self.query_one(ProgressPanel).set_stage(1, "Loading CV...")
        elif stage == "searching":
            self.query_one(ProgressPanel).set_stage(2, "Searching Google & LinkedIn...")
        elif stage == "scoring_jobs":
            top_jobs = data.get("top_jobs", [])
            self.query_one(ProgressPanel).set_stage(3, f"Scored {len(top_jobs)} jobs above threshold")
            for job in top_jobs:
                self.query_one(JobsTable).add_job(job)
        elif stage == "finding_contacts":
            self.query_one(ProgressPanel).set_stage(4, "Finding contacts...")
        elif stage == "scoring_contacts":
            contacts = data.get("contacts", [])
            self.query_one(ProgressPanel).set_stage(5, f"Found {len(contacts)} contacts")
            for contact in contacts:
                self.query_one(ContactsTable).add_contact(contact)
        elif stage == "generating_messages":
            messages = data.get("messages", [])
            self.query_one(ProgressPanel).set_stage(6, f"Generated {len(messages)} messages")
            for msg in messages:
                self.query_one(MessagesPanel).add_message(msg)
        elif stage == "complete":
            self.query_one(ProgressPanel).set_stage(7, "Pipeline complete — press q to exit")
        elif stage == "error":
            self.query_one(ProgressPanel).set_error(data.get("message", "Unknown error"))

    async def _run_pipeline(self) -> None:
        from contacts.clients import ApifyContactClient, VibeProspectingClient
        from contacts.finder import ContactFinder
        from cv.loader import CVLoader
        from cv.parser import CVParser
        from db.connection import create_pool, ensure_schema
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
        from utils.logger import configure_logging

        cfg = self._cfg
        try:
            configure_logging(level=cfg.logging.level)
        except Exception:
            configure_logging()

        pool = None
        try:
            pool = await create_pool(
                host=cfg.database.host,
                port=int(cfg.database.port),
                db=cfg.database.db,
                user=cfg.database.user,
                password=cfg.database.password,
            )
            await ensure_schema(pool)

            llm = ClaudeClient(api_key=cfg.anthropic_api_key)
            apify_contacts = ApifyContactClient(api_token=cfg.apify_api_token)
            vibe_client = VibeProspectingClient(
                api_key=cfg.vibe_api_key, base_url=cfg.vibe_api_base_url
            )
            orch = Orchestrator(
                cv_loader=CVLoader(),
                cv_parser=CVParser(llm=llm),
                google_searcher=GoogleJobSearcher(llm=llm),
                linkedin_searcher=LinkedInJobSearcher(api_token=cfg.apify_api_token),
                combiner=combine_jobs,
                job_scorer=JobScorer(llm=llm),
                contact_finder=ContactFinder(
                    apify_client=apify_contacts,
                    vibe_client=vibe_client,
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
                progress_callback=self._progress_callback,
            )
            filters = SearchFilters(
                keywords=self._keywords or cfg.search.keywords,
                location=cfg.search.location,
                remote=cfg.search.remote,
                onsite=cfg.search.onsite,
                job_type=cfg.search.job_type,
                time_window_hours=cfg.search.time_window_hours,
            )
            ctx = await orch.run(cv_path=self._cv_path, filters=filters)

            if ctx.output:
                Path("output.json").write_text(ctx.output)

        except Exception as exc:
            self.query_one(ProgressPanel).set_error(str(exc))
        finally:
            if pool:
                await pool.close()
