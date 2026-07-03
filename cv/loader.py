import fitz


class CVLoader:
    def load(self, resume: str) -> str:
        doc = fitz.open(resume)
        text = "\n".join([page.get_text() for page in doc])

        return text
