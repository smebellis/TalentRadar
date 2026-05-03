import logging
import sys


_OWN_NAMESPACES = (
    "cli", "pipeline", "search", "scoring", "contacts",
    "cv", "db", "messaging", "ui", "llm", "utils",
)


def configure_logging(level: str = "INFO", fmt: str | None = None) -> None:
    fmt = fmt or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    int_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stdout, level=logging.WARNING, format=fmt, force=True)
    for ns in _OWN_NAMESPACES:
        logging.getLogger(ns).setLevel(int_level)


def get_logger(name: str):
    return logging.getLogger(name)
