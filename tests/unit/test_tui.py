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
