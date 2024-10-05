import sys
import logging
import os

VARLOG_DIR = os.getenv("LC_VAR_LOG_DIR", "/var/log/")
"/var/log/ prefix, can override for searching for another location in testing"


def get_logger_configuration(
    logger=None,
    name_suffix="log_collection_2000",
) -> "logging.Logger":
    "Centralized place for application logs configuration"

    formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        f"{VARLOG_DIR}/log_collection/log_collection.log"
    )
    file_handler.setFormatter(formatter)

    if not logger:
        logger = logging.Logger(name_suffix)
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    return logger
