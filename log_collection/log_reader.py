from argparse import ArgumentParser
import os
from typing import Iterator
from log_collection.utils import get_logger_configuration

logger = get_logger_configuration(name_suffix=__name__)

MAX_RESULT_LINES = int(os.getenv("LC_MAX_RESULT_LINES", 100_000))
"Maximum number of result lines at a time"

# MAX_SCAN_SIZE_BYTES may seem redundant and rarely used compared to MAX_RESULT_LINES,
# it'll act as a short-circuit and provides extra security in case individual log lines have inhumane sizes,
# MAX_RESULT_LINES is easier to reason about representing distinct events.
MAX_SCAN_SIZE_BYTES = int(
    os.getenv("LC_MAX_SCAN_SIZE_BYTES", MAX_RESULT_LINES * 1024 * 1024)
)
"Scan throguh a maximum of ~100GB of logs at a time by default"


class Log_Reader:
    def __init__(self, log_path: str, search_keyword: str, num_of_matches: int) -> None:

        self.log_path = log_path
        "Path to log file we'll be reading from"

        self.search_keyword = search_keyword
        "Needle to search for in logs haystack"

        self.num_of_matches_expected = num_of_matches
        "Number of matches to search for"

    def file_exists(self) -> bool:
        return os.path.isfile(self.log_path) and os.access(self.log_path, os.R_OK)

    def _has_keyword_match(self, line) -> bool:
        return self.search_keyword[::-1] in line

    def get_content(self) -> Iterator[str]:

        try:
            with open(self.log_path, mode="r") as fd:
                # Start from end of log file and work backwards, returning most recent lines first
                fd.seek(0, os.SEEK_END)
                start_position = fd.tell()
                current_position = start_position - 1
                lines_processed = 0
                number_of_matches = 0
                line = ""

                # Search for content here
                # Yield matches, allows user to see results as they're found
                while (
                    current_position >= 0
                    and lines_processed < MAX_RESULT_LINES
                    and start_position - current_position < MAX_SCAN_SIZE_BYTES
                    and number_of_matches < self.num_of_matches_expected
                ):
                    # We can futher optimize IO here by reading larger chunks into a buffer and searching through that
                    fd.seek(current_position)
                    c = fd.read(1)
                    # logger.debug(f"Read char pos: {current_position}, char: '{c}'")
                    line += c
                    if c == "\n" or current_position == 0:
                        if current_position == 0:
                            line += "\n"

                        # Naive search
                        if self.search_keyword is None or self._has_keyword_match(line):
                            number_of_matches += 1
                            yield line[::-1]
                        lines_processed += 1
                        line = ""
                    current_position -= 1
                logger.info(
                    f"Finished reading. Stats: read_lines: {lines_processed}, read_bytes: {start_position - current_position}"
                )
        except FileNotFoundError:
            logger.warning(f"Log file not found: {self.log_path}")
            yield f"Log file not found: {self.log_path}"
        except Exception as e:
            logger.error(
                f"Exception while reading log file: {self.log_path}, exception: {e}"
            )
            yield f"Error while reading log file: {self.log_path}"


if __name__ == "__main__":
    argsParser = ArgumentParser(description="Parse logs")
    argsParser.add_argument("file", help="Log path, e.g. tests/logs/syslog/syslog.log")
    argsParser.add_argument("--keyword", help="Keyword to search for")
    argsParser.add_argument(
        "--n", help="Number of matches to find", type=int, default=1_000_000_000
    )
    args = argsParser.parse_args()
    log_reader = Log_Reader(
        log_path=args.file, search_keyword=args.keyword, num_of_matches=args.n
    )
    [print(line) for line in log_reader.get_content()]
