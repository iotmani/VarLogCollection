from flask import Flask, Response, abort, request
import os
from werkzeug.security import safe_join
from log_collection.utils import get_logger_configuration, VARLOG_DIR
from log_collection.log_reader import Log_Reader, MAX_RESULT_LINES

MAX_SEARCH_KEYWORD_LENGTH = 1000

app = Flask(__name__)
logger = get_logger_configuration(app.logger, name_suffix=__name__)


@app.route("/")
def index():
    return """
<html>
<h3>Usage</h3>
<p>
    Specify a file to view, optionally with a keyword to search for (case sensitive), and n limit of matches.
</p>
<a href="/var/log/syslog/syslog.log?keyword=error&n=3">Example search</a>
</html>
    """


@app.route("/var/log/<path:log_path>")
def view_log(log_path):
    search_keyword = request.args.get("keyword", default=None, type=str)
    n = request.args.get("n", default=MAX_RESULT_LINES, type=int)
    logger.info(
        f"Retrieving logs from {safe_join(log_path)}, search: {search_keyword}, n: {n}, args: {request.args}"
    )
    log_path = safe_join(VARLOG_DIR, log_path) or ""

    # Validate input

    # Check for zipped file extensions
    if os.path.splitext(log_path)[-1] in [".gz", ".zip", ".tar"]:
        abort(400, "Zipped files are not supported")

    if search_keyword is not None:
        if n < 1 or n > MAX_RESULT_LINES:
            abort(400, f"n must be strictly 0 < n < {MAX_RESULT_LINES + 1}")
        if len(search_keyword) < 2 or len(search_keyword) > MAX_SEARCH_KEYWORD_LENGTH:
            abort(
                400,
                f"Search keyword must be strictly 1 < n < {MAX_SEARCH_KEYWORD_LENGTH + 1}",
            )
    reader = Log_Reader(log_path, search_keyword, n)
    if not reader.file_exists():
        return abort(404, "Log file not found")

    # perform search and return results as a stream
    return Response(reader.get_content(), mimetype="text/plain")
