import os
from flask import Flask
from markupsafe import escape
from werkzeug.utils import secure_filename
from log_reader import Log_Reader

app = Flask(__name__)


@app.route("/")
def index():
    return """
<html>
    <h3>Usage</h3>
    <p>
    Specify a file to view, and optionally a keyword to search for (case sensitive), and n number of items.
    <br />
    Note: Results are subject to limits
    </p>
    <a href="/var/log/syslog/syslog.log?keyword=error&n=3">Example search</a>
</html>
    """


@app.route("/var/log/<path:log_path>")
def view_log(log_path):
    log_path = secure_filename(log_path)
    app.logger.debug(f"Request received for {escape(log_path)}")
    reader = Log_Reader(log_path=log_path)
    return f"<body style='background-color: black; color: yellow;'>Logs to {escape(log_path)}</body>"
