import logging

from utils.logger import get_logger


def test_get_logger_returns_logger_instance():
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)


def test_get_logger_uses_provided_name():
    logger = get_logger("my.custom.name")
    assert logger.name == "my.custom.name"


def test_get_logger_different_names_return_different_loggers():
    logger_a = get_logger("module.a")
    logger_b = get_logger("module.b")
    assert logger_a is not logger_b
