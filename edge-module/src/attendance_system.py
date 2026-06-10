import cv2
import face_recognition
import numpy as np
import csv
from datetime import datetime, date
import os
import time
from send_period_from_csv import send_period


from config import (
    ENCODINGS_FILE, NAMES_FILE,
    ATTENDANCE_FILE, CAMERA_INDEX, TOLERANCE, LOGS_DIR,
    PERIOD_TIMINGS, ATTENDANCE_WINDOW_MIN, PROCESS_EVERY_SECONDS
)

# ================= TIME HELPERS =================

def time_to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m

PERIODS = [(time_to_minutes(s), time_to_minutes(e)) for s, e in PERIOD_TIMINGS]
ATTENDANCE_WINDOW = ATTENDANCE_WINDOW_MIN

# ================= DATA FUNCTIONS =================

def load_data():
    if not (os.path.exists(ENCODINGS_FILE) and os.path.exists(NAMES_FILE)):
        raise FileNotFoundError("Run register_faces.py first.")
    known_encodings = np.load(ENCODINGS_FILE, allow_pickle=True).tolist()
    known_names = np.load(NAMES_FILE, allow_pickle=True).tolist()
    print(f"[INFO] Loaded {len(known_names)} known faces.")
    return known_encodings, known_names

# ========== DAILY LOG FILE (FROM SCRIPT 1) ==========

def write_header_if_needed():
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "time", "name", "status"])
        print(f"[INFO] Created new attendance file: {ATTENDANCE_FILE}")

def log_attendance(name, status="Present"):
    write_header_if_needed()
    now = datetime.now()
    with open(ATTENDANCE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            name,
            status
        ])
    print(f"[LOG] {name} marked as {status}")

# ========== PERIOD CSV (FROM SCRIPT 2) ==========

def get_today_file():
    os.makedirs(LOGS_DIR, exist_ok=True)
    fname = f"attendance_{date.today()}.csv"
    return os.path.join(LOGS_DIR, fname)

def init_csv_if_needed():
    file = get_today_file()
    if not os.path.exists(file):
        with open(file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "period", "name", "status", "time"])
    return file

def save_period_attendance(period_no, attendance_status):
    file = init_csv_if_needed()
    now = datetime.now().strftime("%H:%M:%S")
    today = date.today().isoformat()

    with open(file, "a", newline="") as f:
        writer = csv.writer(f)
        for name, status in attendance_status.items():
            writer.writerow([today, period_no, name, status, now])

    print(f"[SAVED] Period {period_no} attendance saved.")

# ================= PERIOD LOGIC =================

def get_current_period_index():
    now = datetime.now()
    now_min = now.hour * 60 + now.minute

    for i, (start, end) in enumerate(PERIODS):
        if start <= now_min < end:
            return i
    return None

def minutes_into_period(period_index):
    start, _ = PERIODS[period_index]
    now = datetime.now()
    now_min = now.hour * 60 + now.minute
    return now_min - start

# ================= MAIN =================

def main():
    print("[INFO] Loading known faces...")
    known_encodings, known_names = load_data()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise IOError("Camera not opened")

    print("[INFO] Smart Attendance System Started")

    last_process_time = 0
    display_frame = None

    attendance_status_global = {n: "Absent" for n in set(known_names)}

    current_period = None
    attendance_status_period = None

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] Frame read failed.")
            break

        now_time = time.time()

        if display_frame is None or (now_time - last_process_time) >= PROCESS_EVERY_SECONDS:
            last_process_time = now_time
            display_frame = frame.copy()

            # ============ PERIOD CHECK ============
            period_idx = get_current_period_index()

            if period_idx is not None:
                if current_period != period_idx:
                    if attendance_status_period is not None:
                        finished_period = current_period + 1

                        save_period_attendance(finished_period, attendance_status_period)

                        # 🔥 SEND TO RASPBERRY PI HERE
                        csv_file = get_today_file()
                        send_period(csv_file, finished_period)

                    current_period = period_idx
                    attendance_status_period = {n: "Absent" for n in set(known_names)}
                    print(f"\n[NEW PERIOD] Period {current_period + 1} started")


            # ============ FACE PROCESSING ============
            small = cv2.resize(display_frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            locations = face_recognition.face_locations(rgb_small)
            encodings = face_recognition.face_encodings(rgb_small, locations)

            if current_period is not None:
                min_passed = minutes_into_period(current_period)
            else:
                min_passed = 0

            for enc, loc in zip(encodings, locations):
                matches = face_recognition.compare_faces(known_encodings, enc, tolerance=TOLERANCE)
                distances = face_recognition.face_distance(known_encodings, enc)

                name = "Unknown"
                if len(distances) > 0:
                    best_idx = np.argmin(distances)
                    if matches[best_idx]:
                        name = known_names[best_idx]

                top, right, bottom, left = loc
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2

                color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)

                cv2.rectangle(display_frame, (left, top), (right, bottom), color, 2)
                cv2.putText(display_frame, name, (left, bottom + 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                # ============ GLOBAL ATTENDANCE ============
                if name != "Unknown" and attendance_status_global[name] != "Present":
                    attendance_status_global[name] = "Present"
                    log_attendance(name, "Present")

                # ============ PERIOD ATTENDANCE ============
                if name != "Unknown" and current_period is not None:
                    if min_passed <= ATTENDANCE_WINDOW:
                        if attendance_status_period[name] != "Present":
                            attendance_status_period[name] = "Present"
                            print(f"[P{current_period+1}] {name} -> Present")

        # Always show frame
        if display_frame is not None:
            cv2.imshow("Face Attendance", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Save last period
    if current_period is not None and attendance_status_period is not None:
        save_period_attendance(current_period + 1, attendance_status_period)

        csv_file = get_today_file()
        send_period(csv_file, current_period + 1)


    cap.release()
    cv2.destroyAllWindows()

    print("\n[INFO] FINAL GLOBAL ATTENDANCE:")
    for n, st in attendance_status_global.items():
        print(f" - {n}: {st}")

    print("[INFO] Program ended.")

if __name__ == "__main__":
    main()
