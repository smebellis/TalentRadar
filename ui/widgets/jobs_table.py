from textual.app import ComposeResult
from textual.widgets import DataTable, Static


class JobsTable(Static):
    def compose(self) -> ComposeResult:
        yield DataTable(id="jobs-dt")

    def on_mount(self) -> None:
        self.query_one("#jobs-dt", DataTable).add_columns(
            "Role", "Company", "Score", "Source"
        )

    def add_job(self, job) -> None:
        dt = self.query_one("#jobs-dt", DataTable)
        score = f"{job.fit_score:.1f}" if job.fit_score is not None else "N/A"
        dt.add_row(job.title[:30], job.company[:20], score, job.source)
