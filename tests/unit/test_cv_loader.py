from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cv.loader import CVLoader


def test_cv_loader_returns_text_from_pdf():
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Page one text"
    mock_doc = MagicMock()
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

    with patch("cv.loader.fitz.open", return_value=mock_doc):
        loader = CVLoader()
        result = loader.load("resume.pdf")

    assert "Page one text" in result


def test_cv_loader_concatenates_multiple_pages():
    pages = [MagicMock(), MagicMock()]
    pages[0].get_text.return_value = "Page one"
    pages[1].get_text.return_value = "Page two"
    mock_doc = MagicMock()
    mock_doc.__iter__ = MagicMock(return_value=iter(pages))

    with patch("cv.loader.fitz.open", return_value=mock_doc):
        loader = CVLoader()
        result = loader.load("resume.pdf")

    assert "Page one" in result
    assert "Page two" in result


def test_cv_loader_raises_on_missing_file():
    with patch("cv.loader.fitz.open", side_effect=FileNotFoundError):
        loader = CVLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("missing.pdf")
