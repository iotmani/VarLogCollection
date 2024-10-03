from flask import Flask, Response, abort

from markupsafe import escape
from werkzeug.security import safe_join
from .utils import get_logger_configuration
from .log_reader import Log_Reader

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
    log_path = safe_join(log_path)
    app.logger.debug(f"Retrieving logs from {escape(log_path)}")
    reader = Log_Reader(log_path=log_path)
    if not reader.file_exists():
        return abort(404)
    return Response(reader.get_content(), mimetype="text/plain")
