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
