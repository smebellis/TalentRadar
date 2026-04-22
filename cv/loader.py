from typing import LiteralString

import fitz


class CVLoader:
    def load(self, resume: str) -> LiteralString:
        doc = fitz.open(resume, filetype="txt")
        text = "\n".join([page.get_text() for page in doc])

        return text
