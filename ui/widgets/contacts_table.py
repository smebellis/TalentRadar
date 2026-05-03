from textual.app import ComposeResult
from textual.widgets import DataTable, Static


class ContactsTable(Static):
    def compose(self) -> ComposeResult:
        yield DataTable(id="contacts-dt")

    def on_mount(self) -> None:
        self.query_one("#contacts-dt", DataTable).add_columns(
            "Name", "Title", "Company"
        )

    def add_contact(self, contact) -> None:
        dt = self.query_one("#contacts-dt", DataTable)
        dt.add_row(contact.name[:25], contact.title[:25], contact.company[:20])
