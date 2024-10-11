from argparse import ArgumentParser
import os
from typing import Iterator

from log_collection.utils import get_logger_configuration

logger = get_logger_configuration(name_suffix=__name__)

MAX_RESULT_LINES = int(os.getenv("LC_MAX_RESULT_LINES", 100_000_000))
"Maximum number of result lines at a time"

# MAX_SCAN_SIZE_BYTES may seem redundant and rarely used compared to MAX_RESULT_LINES,
# it'll act as a short-circuit and provides extra security in case individual log lines have inhumane sizes,
# MAX_RESULT_LINES is easier to reason about representing distinct events.
MAX_SCAN_SIZE_BYTES = int(
    os.getenv("LC_MAX_SCAN_SIZE_BYTES", MAX_RESULT_LINES * 1024 * 1024)
)
"Scan throguh a maximum of ~100GB of logs at a time by default"


BLOCK_SIZE = 2 * 1024 * 1024
"2Mb default block size to read at a time"


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
        # TODO: pre-process the search keyword and Implement Knuth–Morris–Pratt
        return self.search_keyword in line

    def get_content(self) -> Iterator[str]:

        try:
            with open(self.log_path, mode="r") as fd:
                # Start from end of log file and work backwards, returning most recent lines first
                fd.seek(0, os.SEEK_END)
                start_position = fd.tell()
                current_position = max(0, start_position - BLOCK_SIZE)
                lines_processed = 0
                number_of_matches = 0

                # Yield matches, allows user to see results as they're found
                while (
                    current_position >= 0
                    and lines_processed < MAX_RESULT_LINES
                    and start_position - current_position < MAX_SCAN_SIZE_BYTES
                    and number_of_matches < self.num_of_matches_expected
                ):
                    # Start reading from the end, we want last lines first
                    fd.seek(current_position)
                    # Optimize IO by reading larger chunks into a buffer and searching through that
                    block_read = fd.read(BLOCK_SIZE)

                    # If nothing read, nothing to do
                    if not block_read:
                        break

                    next_newline_pos = block_read.find("\n")

                    # In case we jump into the middle of a line, move cursor's current_position to the next "\n"
                    # so the next block will end on a new line:
                    # Block1: ...ABCD\nEFGH\nIJK -> EFGH\nIJK [EOF]
                    # Block2: [start] 1235\nABCD\n
                    if current_position != 0:
                        if next_newline_pos != -1:
                            current_position = max(
                                0,
                                (current_position - len(block_read) + next_newline_pos),
                            )
                        else:
                            current_position -= len(block_read)
                            next_newline_pos = 0

                    # Split block read into separate lines, in reversed order making last one top
                    for line_read in block_read.split("\n")[::-1]:
                        # Naive search
                        if self.search_keyword is None or self._has_keyword_match(
                            line_read
                        ):
                            number_of_matches += 1
                            yield line_read + "\n"
                        lines_processed += 1

                        if number_of_matches >= self.num_of_matches_expected:
                            break

                    # All done reading
                    if current_position == 0:
                        break

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
