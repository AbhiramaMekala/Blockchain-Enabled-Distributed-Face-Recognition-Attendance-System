import cv2
import face_recognition
import numpy as np
import csv
from datetime import datetime
import os
from config import (
    ENCODINGS_FILE, NAMES_FILE,
    ATTENDANCE_FILE, CAMERA_INDEX, TOLERANCE, LOGS_DIR
)

def load_data():
    if not (os.path.exists(ENCODINGS_FILE) and os.path.exists(NAMES_FILE)):
        raise FileNotFoundError("Run register_faces.py first.")
    known_encodings = np.load(ENCODINGS_FILE, allow_pickle=True).tolist()
    known_names = np.load(NAMES_FILE, allow_pickle=True).tolist()
    return known_encodings, known_names

def write_header_if_needed():
    os.makedirs(LOGS_DIR, exist_ok=True)
    if not os.path.exists(ATTENDANCE_FILE):
        with open(ATTENDANCE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "time", "name", "status"])

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

def main():
    print("[INFO] Loading known faces...")
    known_encodings, known_names = load_data()
    attendance_status = {n: "Absent" for n in set(known_names)}

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        raise IOError("Cannot open camera.")
    print("[INFO] Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame read failed.")
            break

        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_small = small[:, :, ::-1]

        locations = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, locations)

        for enc, loc in zip(encodings, locations):
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=TOLERANCE)
            distances = face_recognition.face_distance(known_encodings, enc)

            name = "Unknown"
            if len(distances) > 0:
                best_idx = np.argmin(distances)
                if matches[best_idx]:
                    name = known_names[best_idx]

            top, right, bottom, left = loc
            top *= 2; right *= 2; bottom *= 2; left *= 2

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, name, (left, bottom + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if name != "Unknown" and attendance_status.get(name) != "Present":
                attendance_status[name] = "Present"
                print(f"[ATTENDANCE] {name} → Present")
                log_attendance(name, "Present")

        y = 20
        for n, st in attendance_status.items():
            txt = f"{n}: {st}"
            col = (0, 255, 0) if st == "Present" else (0, 0, 255)
            cv2.putText(frame, txt, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
            y += 25

        cv2.imshow("Face Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Final status:")
    for n, st in attendance_status.items():
        print(f" - {n}: {st}")

if __name__ == "__main__":
    main()
