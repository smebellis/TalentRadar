import pytest

from textual.widgets import Label, ProgressBar


@pytest.mark.asyncio
async def test_progress_panel_set_stage_updates_label():
    from ui.widgets.progress_panel import ProgressPanel
    from textual.app import App, ComposeResult

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ProgressPanel(id="progress")

    app = TestApp()
    async with app.run_test(size=(80, 10)) as pilot:
        panel = app.query_one(ProgressPanel)
        panel.set_stage(3, "Scoring jobs")
        await pilot.pause()
        label = app.query_one("#progress-label", Label)
        assert "3" in str(label.content)
        assert "Scoring jobs" in str(label.content)


@pytest.mark.asyncio
async def test_progress_panel_set_error_shows_error_text():
    from ui.widgets.progress_panel import ProgressPanel
    from textual.app import App, ComposeResult

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ProgressPanel(id="progress")

    app = TestApp()
    async with app.run_test(size=(80, 10)) as pilot:
        panel = app.query_one(ProgressPanel)
        panel.set_error("Something broke")
        await pilot.pause()
        label = app.query_one("#progress-label", Label)
        content = str(label.content)
        assert "Something broke" in content


@pytest.mark.asyncio
async def test_jobs_table_add_job_appends_row():
    from ui.widgets.jobs_table import JobsTable
    from textual.app import App, ComposeResult
    from textual.widgets import DataTable
    from unittest.mock import MagicMock

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield JobsTable(id="jobs")

    app = TestApp()
    async with app.run_test(size=(120, 20)) as pilot:
        job = MagicMock()
        job.title = "Senior Engineer"
        job.company = "Acme Corp"
        job.fit_score = 8.5
        job.source = "linkedin"

        table = app.query_one(JobsTable)
        table.add_job(job)
        await pilot.pause()

        dt = app.query_one("#jobs-dt", DataTable)
        assert dt.row_count == 1


@pytest.mark.asyncio
async def test_contacts_table_add_contact_appends_row():
    from ui.widgets.contacts_table import ContactsTable
    from textual.app import App, ComposeResult
    from textual.widgets import DataTable
    from unittest.mock import MagicMock

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield ContactsTable(id="contacts")

    app = TestApp()
    async with app.run_test(size=(120, 20)) as pilot:
        contact = MagicMock()
        contact.name = "Jane Smith"
        contact.title = "Engineering Manager"
        contact.company = "Acme Corp"

        table = app.query_one(ContactsTable)
        table.add_contact(contact)
        await pilot.pause()

        dt = app.query_one("#contacts-dt", DataTable)
        assert dt.row_count == 1


@pytest.mark.asyncio
async def test_messages_panel_add_message_writes_to_log():
    from ui.widgets.messages_panel import MessagesPanel
    from textual.app import App, ComposeResult
    from textual.widgets import RichLog

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield MessagesPanel(id="messages")

    app = TestApp()
    async with app.run_test(size=(120, 20)) as pilot:
        panel = app.query_one(MessagesPanel)
        from db.models.message import Message
        import uuid
        msg = Message(contact_id=uuid.uuid4(), job_id=uuid.uuid4(), message_text="Hi Jane, I saw your role at Acme Corp...")
        panel.add_message(msg)
        await pilot.pause()
        log = app.query_one("#messages-log", RichLog)
        assert log is not None


def _mock_cfg():
    from unittest.mock import MagicMock
    cfg = MagicMock()
    cfg.logging.level = "INFO"
    cfg.database.host = "localhost"
    cfg.database.port = "5432"
    cfg.database.db = "test"
    cfg.database.user = "test"
    cfg.database.password = "test"
    cfg.anthropic_api_key = "test-key"
    cfg.apify_api_token = "test-token"
    cfg.vibe_api_key = "test-vibe-key"
    cfg.vibe_api_base_url = ""
    cfg.scoring.max_contacts_per_category = 5
    cfg.scoring.contact_score_threshold = 5.0
    cfg.scoring.veteran_score_boost = 1.0
    cfg.scoring.job_score_threshold = 7.0
    cfg.scoring.top_n_jobs = 5
    cfg.search.keywords = ["python"]
    cfg.search.location = "Denver, CO"
    cfg.search.remote = True
    cfg.search.onsite = False
    cfg.search.job_type = "full_time"
    cfg.search.time_window_hours = 48
    return cfg


@pytest.mark.asyncio
async def test_job_search_app_mounts_all_panels():
    from ui.tui import JobSearchApp
    from ui.widgets.progress_panel import ProgressPanel
    from ui.widgets.jobs_table import JobsTable
    from ui.widgets.contacts_table import ContactsTable
    from ui.widgets.messages_panel import MessagesPanel

    app = JobSearchApp(cfg=_mock_cfg(), cv_path="test.pdf", keywords=[], _skip_pipeline=True)
    async with app.run_test(size=(120, 40)) as pilot:
        assert app.query_one(ProgressPanel) is not None
        assert app.query_one(JobsTable) is not None
        assert app.query_one(ContactsTable) is not None
        assert app.query_one(MessagesPanel) is not None


@pytest.mark.asyncio
async def test_job_search_app_q_exits():
    from ui.tui import JobSearchApp

    app = JobSearchApp(cfg=_mock_cfg(), cv_path="test.pdf", keywords=[], _skip_pipeline=True)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.press("q")
    # Reaching here means the app exited cleanly
