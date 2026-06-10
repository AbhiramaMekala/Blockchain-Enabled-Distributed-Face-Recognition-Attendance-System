from flask import Flask, request, jsonify
import sqlite3

DB_FILE = "attendance.db"

app = Flask(__name__)

@app.route("/upload_period_csv", methods=["POST"])
def upload_period_csv():
    payload = request.json

    date = payload["date"]
    period = int(payload["period"])
    rows = payload["rows"]

    col = f"period{period}"

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    for row in rows:
        sid = row["name"]
        status = 1 if row["status"] == "Present" else 0

        # Ensure row exists
        cur.execute("""
            INSERT OR IGNORE INTO attendance (date, stdid)
            VALUES (?, ?)
        """, (date, sid))

        # Update only this period column
        cur.execute(f"""
            UPDATE attendance
            SET {col} = ?
            WHERE date = ? AND stdid = ?
        """, (status, date, sid))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Period saved",
        "date": date,
        "period": period,
        "rows": len(rows)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
