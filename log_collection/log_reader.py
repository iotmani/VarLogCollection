import os
from typing import Iterator
from .utils import get_logger_configuration, VARLOG_DIR

logger = get_logger_configuration(name_suffix=__name__)


class Log_Reader:
    def __init__(self, log_path: str) -> None:

        self.MAX_RESULT_LINES = int(os.getenv("LC_MAX_RESULT_LINES", 10_000))
        "Return maximum of 10k results at a time"

        # MAX_SCAN_SIZE_BYTES may seem redundant and rarely used compared to MAX_RESULT_LINES,
        # it'll act as a short-circuit and provides extra security in case individual log lines have inhumane sizes,
        # MAX_RESULT_LINES is easier to reason about representing distinct events.
        self.MAX_SCAN_SIZE_BYTES = int(
            os.getenv("LC_MAX_SCAN_SIZE_BYTES", self.MAX_RESULT_LINES * 1024 * 1024)
        )
        "Scan throguh a maximum of ~10GB of logs at a time by default"

        self.log_path = os.path.join(VARLOG_DIR, log_path)
        "Path to log file we'll be reading from"

    def file_exists(self) -> bool:
        return os.path.isfile(self.log_path) and os.access(self.log_path, os.R_OK)

    def get_content(self) -> Iterator[str]:
        try:
            with open(self.log_path, mode="r") as fd:
                # Start from end of log file and work backwards, returning most recent lines first
                fd.seek(0, os.SEEK_END)
                start_position = fd.tell()
                current_position = start_position
                lines_processed = 0
                line = ""

                # Search for content here
                # Yield matches, allows user to see results as they're found
                logger.debug(
                    f"{current_position} >= 0 and {lines_processed} < {self.MAX_RESULT_LINES} and {start_position} - {current_position} < {self.MAX_SCAN_SIZE_BYTES}"
                )
                while (
                    current_position >= 0
                    and lines_processed < self.MAX_RESULT_LINES
                    and start_position - current_position < self.MAX_SCAN_SIZE_BYTES
                ):
                    fd.seek(current_position)
                    c = fd.read(1)
                    line += c
                    if c == "\n":
                        yield line[::-1]
                        lines_processed += 1
                        line = ""
                    current_position -= 1
                logger.debug(f"Finished reading. current_position: {current_position}")
        except FileNotFoundError:
            logger.warning(f"Log file not found: {self.log_path}")
            yield f"Log file not found: {self.log_path}"
        except Exception as e:
            logger.error(
                f"Exception while reading log file: {self.log_path}, exception: {e}"
            )
            yield f"Error while reading log file: {self.log_path}"
