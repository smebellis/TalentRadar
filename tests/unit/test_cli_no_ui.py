import sys
from unittest.mock import MagicMock, patch

import pytest


def test_no_ui_flag_runs_headless(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "full", "--cv", "/tmp/resume.pdf", "--no-ui"])

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=None)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("cli.initialize", return_value=mock_ctx), \
         patch("cli.compose", return_value=MagicMock()), \
         patch("asyncio.run") as mock_async_run, \
         patch("cli.JobSearchApp") as mock_app:
        from cli import main
        main()

    mock_async_run.assert_called_once()
    mock_app.assert_not_called()


def test_without_no_ui_flag_launches_tui(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "full", "--cv", "/tmp/resume.pdf"])

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=None)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    mock_app_instance = MagicMock()

    with patch("cli.initialize", return_value=mock_ctx), \
         patch("cli.compose", return_value=MagicMock()), \
         patch("asyncio.run") as mock_async_run, \
         patch("cli.JobSearchApp", return_value=mock_app_instance) as mock_app_cls:
        from cli import main
        main()

    mock_app_cls.assert_called_once()
    mock_app_instance.run.assert_called_once()
    mock_async_run.assert_not_called()
