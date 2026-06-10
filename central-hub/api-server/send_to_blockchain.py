import json
import requests
import sys
import os
import base64

NODE = "http://127.0.0.1:26657"

if len(sys.argv) < 2:
    print("Usage: python send_to_blockchain.py attendance_file.json")
    exit(1)

filename = sys.argv[1]

if not os.path.exists(filename):
    print("File not found:", filename)
    exit(1)

with open(filename, "r") as f:
    data = json.load(f)

if not isinstance(data, list):
    print("JSON must contain array of records")
    exit(1)

print("Sending", len(data), "records to blockchain...")

for rec in data:
    tx_json = json.dumps(rec, separators=(',', ':')).encode()
    tx_base64 = base64.b64encode(tx_json).decode()

    payload = {
        "jsonrpc": "2.0",
        "method": "broadcast_tx_commit",
        "id": 1,
        "params": {
            "tx": tx_base64
        }
    }

    r = requests.post(NODE, json=payload)
    res = r.json()

    if "error" in res:
        print("❌ Failed:", rec)
        print(res)
    else:
        print("✔ Sent:", rec["stdid"])

print("Done.")
