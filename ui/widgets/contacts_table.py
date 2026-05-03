from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import DataTable, Static


class ContactsTable(Static):
    def compose(self) -> ComposeResult:
        yield DataTable(id="contacts-dt")

    def on_mount(self) -> None:
        self.query_one("#contacts-dt", DataTable).add_columns(
            "Name", "Title", "Company", "LinkedIn"
        )

    def add_contact(self, contact) -> None:
        dt = self.query_one("#contacts-dt", DataTable)
        linkedin = (
            Text("Profile", style=f"link {contact.linkedin_url}")
            if contact.linkedin_url
            else Text("—")
        )
        dt.add_row(contact.name[:25], contact.title[:25], contact.company[:20], linkedin)
