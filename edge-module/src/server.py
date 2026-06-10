from flask import Flask, jsonify, send_from_directory
import csv
import os
from collections import OrderedDict
from config import ATTENDANCE_FILE, WEB_DIR, NAMES_FILE
import numpy as np

app = Flask(__name__, static_folder=WEB_DIR, static_url_path="")

def get_all_registered_names():
    if os.path.exists(NAMES_FILE):
        names = np.load(NAMES_FILE, allow_pickle=True).tolist()
        return sorted(set(names))
    return []

def get_latest_attendance():
    """
    Reads logs/attendance.csv and returns latest status per person.
    Default: Absent, unless marked Present in log.
    """
    latest = OrderedDict()
    registered = get_all_registered_names()
    for name in registered:
        latest[name] = "Absent"

    if not os.path.exists(ATTENDANCE_FILE):
        return latest

    with open(ATTENDANCE_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            status = row["status"]
            if name in latest:
                latest[name] = status

    return latest

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/script.js")
def script_js():
    return send_from_directory(app.static_folder, "script.js")

@app.route("/style.css")
def style_css():
    return send_from_directory(app.static_folder, "style.css")

@app.route("/api/attendance/latest")
def api_latest():
    latest = get_latest_attendance()
    data = [{"name": n, "status": s} for n, s in latest.items()]
    return jsonify(data)

if __name__ == "__main__":
    # Runs on http://localhost:5000
    app.run(host="0.0.0.0", port=5000, debug=True)
