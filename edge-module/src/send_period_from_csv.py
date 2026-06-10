import csv
import requests
import os

PI_IP = "100.73.59.102"
URL = f"http://{PI_IP}:5000/upload_period_csv"

def send_period(csv_file, period_no):
    rows_to_send = []
    date_value = None

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row["period"]) == period_no:
                if date_value is None:
                    date_value = row["date"]   # ✅ GET DATE FROM CSV

                rows_to_send.append({
                    "name": row["name"],
                    "status": row["status"]
                })

    if not rows_to_send:
        print("[WARN] No rows found for this period")
        return

    payload = {
        "date": date_value,        # ✅ NOW DATE WILL NOT BE NULL
        "period": period_no,
        "rows": rows_to_send
    }

    print("[DEBUG] Sending JSON:", payload)

    try:
        r = requests.post(URL, json=payload, timeout=10)
        print("[PI SYNC]", r.json())
    except Exception as e:
        print("[PI ERROR]", e)
