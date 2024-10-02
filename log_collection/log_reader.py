import os
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

    def get_content(self) -> None:
        try:
            with open(self.log_path, mode="r") as fd:

                # Start from end of log file and work backwards return most recent first
                fd.seek(0, os.SEEK_END)

                start_position = fd.tell()
                current_position = start_position
                lines_processed = 0

                line = ""

                logger.debug(
                    f"{current_position} >= 0 and {lines_processed} < {self.MAX_RESULT_LINES} and {start_position} - {current_position} < {self.MAX_SCAN_SIZE_BYTES}"
                )
                # Search for content here
                # Yield matches, allows user to see results as they're found
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
                logger.debug(f"All done reading. current_position: {current_position}")
        except FileNotFoundError as e:
            logger.info(f"Log path doesn't exist: {self.log_path}")
            raise e
