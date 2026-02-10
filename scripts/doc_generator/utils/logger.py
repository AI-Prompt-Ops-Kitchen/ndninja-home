"""Logging setup for documentation generator"""
import logging
import sys
from config import Config


def setup_logger(name='doc_generator'):
    """
    Setup and configure logger

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, Config.LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(Config.LOG_FORMAT)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger
