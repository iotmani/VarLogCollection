import os
import logging


class Log_Reader:
    def __init__(self, log_path: str) -> None:
        "/var/log/ prefix, can override for searching for another location in testing"
        self.VARLOG_DIR = os.getenv("LC_VAR_LOG_DIR", "/var/log/")

        "Scan throguh a maximum of 10GB at a time"
        self.MAX_SCAN_SIZE_MB = os.getenv("LC_MAX_SCAN_SIZE_MB", 1024 * 10)

        "Return maximum of 10k results at a time"
        self.MAX_RESULT_LINES = os.getenv("LC_MAX_RESULT_LINES", 10_000)

        "Path to log within /var/log/"
        self.log_path = log_path

        logging.basicConfig(
            level=logging.DEBUG,
            filename=f"{self.VARLOG_DIR}/log_collection/log_collection.log",
        )
        self.logger = logging.getLogger(__name__)

    def _read_content(self) -> None:
        try:
            with open(self.log_path, mode="r") as fd:
                # Start from end to get most recent
                fd.seek(0, os.SEEK_END)

                # Search for content here
        except FileNotFoundError as e:
            self.logger.info(f"Log path doesn't exist: {self.log_path}")
            raise e

    def search_keyword(self, keyword: str, count=0):
        self.logger.info(f"Searching for: {keyword}, n: {count}")
