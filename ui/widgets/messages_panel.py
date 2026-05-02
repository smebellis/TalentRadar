from textual.app import ComposeResult
from textual.widgets import RichLog, Static


class MessagesPanel(Static):
    def compose(self) -> ComposeResult:
        yield RichLog(id="messages-log", markup=True, wrap=True)

    def add_message(self, message: str) -> None:
        self.query_one("#messages-log", RichLog).write(message)
