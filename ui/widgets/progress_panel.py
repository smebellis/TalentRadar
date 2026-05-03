from textual.app import ComposeResult
from textual.widgets import Label, ProgressBar, Static


class ProgressPanel(Static):
    def compose(self) -> ComposeResult:
        yield Label("Pipeline Progress", id="progress-title")
        yield ProgressBar(total=7, show_percentage=False, id="progress-bar")
        yield Label("Waiting to start...", id="progress-label")

    def set_stage(self, n: int, label: str) -> None:
        self.query_one("#progress-bar", ProgressBar).update(progress=n)
        self.query_one("#progress-label", Label).update(f"[{n}/7] {label}")

    def set_error(self, message: str) -> None:
        self.query_one("#progress-label", Label).update(f"[red]Error: {message}[/red]")
