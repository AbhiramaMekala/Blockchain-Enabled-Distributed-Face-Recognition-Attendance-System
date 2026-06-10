import sqlite3
import json
import hashlib
from datetime import datetime
import os

# Always use absolute path (important for cron)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "attendance.db")

def export_and_clear():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # Fetch all data
    cur.execute("SELECT * FROM attendance")
    rows = cur.fetchall()

    if not rows:
        print("[INFO] No data to export.")
        conn.close()
        return

    # Get column names
    col_names = [description[0] for description in cur.description]

    # Convert to JSON format
    data = []
    for row in rows:
        data.append(dict(zip(col_names, row)))

    # Create file name with date
    today = datetime.now().strftime("%Y-%m-%d")
    filename = os.path.join(BASE_DIR, f"attendance_{today}.json")

    with open(filename, "w") as f:
        json.dump(data, f, indent=2, sort_keys=True)

    print(f"[OK] Data exported to {filename}")

    # Generate hash
    json_string = json.dumps(data, sort_keys=True)
    daily_hash = hashlib.sha256(json_string.encode()).hexdigest()

    print("[HASH]", daily_hash)

    # TODO: Send daily_hash to Tendermint here

    # Clear table
    cur.execute("DELETE FROM attendance")
    conn.commit()

    print("[OK] Database cleared for next day.")

    conn.close()

if __name__ == "__main__":
    export_and_clear()
