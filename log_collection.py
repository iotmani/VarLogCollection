from flask import Flask

app = Flask(__name__)


@app.route("/var/log/")
def logs():
    return "<p>Some logs!</p"
