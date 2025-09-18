
import logging
import sys


def setup_logging(level: str = "INFO"):
    logger = logging.getLogger("worker")
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
