import cv2
import face_recognition
import numpy as np
import os
from config import ENCODINGS_FILE, NAMES_FILE

dispW = 640
dispH = 480
flip = 4

camSet = (
    'nvarguscamerasrc ! '
    'video/x-raw(memory:NVMM), width=3264, height=2464, format=NV12, framerate=21/1 ! '
    f'nvvidconv flip-method={flip} ! '
    f'video/x-raw, width={dispW}, height={dispH}, format=BGRx ! '
    'videoconvert ! video/x-raw, format=BGR ! appsink'
)


def capture_face_images(name, num_images=5):
    print(f"[INFO] Using camera pipeline:\n{camSet}\n")
    cap = cv2.VideoCapture(camSet)

    if not cap.isOpened():
        print("[ERROR] Could not open camera with given GStreamer pipeline.")
        return []

    count = 0
    print(f"[INFO] Capturing images for {name}...")
    print("Press 'c' to capture an image, 'q' to quit.")

    images = []

    while count < num_images:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to grab frame")
            break

        cv2.putText(frame, f"{name} (press 'c')", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Capture Faces", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            images.append(frame.copy())
            count += 1
            print(f"[INFO] Captured image {count}/{num_images}")
        elif key == ord('q'):
            print("[INFO] User requested quit during capture.")
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Total images captured: {len(images)}")
    return images


def encode_faces(images):
    encodings = []
    print(f"[INFO] Encoding faces from {len(images)} image(s)...")

    for idx, img in enumerate(images):
        if img is None or img.size == 0:
            print(f"[WARN] Image {idx+1} is empty, skipping.")
            continue

        # ✅ Safe BGR → RGB conversion
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Detect face locations
        boxes = face_recognition.face_locations(rgb_img)
        if not boxes:
            print(f"[WARN] No face in image {idx+1}, skipping.")
            continue

        # Get encodings for all faces found in this image
        face_encs = face_recognition.face_encodings(rgb_img, boxes)
        if not face_encs:
            print(f"[WARN] Could not encode face in image {idx+1}, skipping.")
            continue

        # Take the first face encoding
        encodings.append(face_encs[0])
        print(f"[INFO] Encoded face from image {idx+1}")

    print(f"[INFO] Total encodings created: {len(encodings)}")
    return encodings


def load_existing_data():
    if os.path.exists(ENCODINGS_FILE) and os.path.exists(NAMES_FILE):
        known_encodings = np.load(ENCODINGS_FILE, allow_pickle=True).tolist()
        known_names = np.load(NAMES_FILE, allow_pickle=True).tolist()
        print(f"[INFO] Loaded {len(known_names)} existing faces.")
    else:
        known_encodings, known_names = [], []
        print("[INFO] No existing data found, starting fresh.")
    return known_encodings, known_names


def save_data(encodings, names):
    # Make sure directory exists (for both files)
    enc_dir = os.path.dirname(ENCODINGS_FILE)
    name_dir = os.path.dirname(NAMES_FILE)

    if enc_dir:
        os.makedirs(enc_dir, exist_ok=True)
    if name_dir and name_dir != enc_dir:
        os.makedirs(name_dir, exist_ok=True)

    np.save(ENCODINGS_FILE, np.array(encodings, dtype=object))
    np.save(NAMES_FILE, np.array(names, dtype=object))

    print("[INFO] Saved encodings & names.")
    print(f"[INFO] Encodings file: {os.path.abspath(ENCODINGS_FILE)}")
    print(f"[INFO] Names file:     {os.path.abspath(NAMES_FILE)}")

    # Small sanity check
    if os.path.exists(ENCODINGS_FILE) and os.path.exists(NAMES_FILE):
        print("[INFO] ✅ Save verified: both files exist.")
    else:
        print("[ERROR] ❌ Save failed: files not found after saving!")


if __name__ == "__main__":
    person_name = input("Enter name: ").strip()
    if not person_name:
        print("Name cannot be empty.")
        exit(0)

    images = capture_face_images(person_name, num_images=5)
    if not images:
        print("No images captured.")
        exit(0)

    new_encodings = encode_faces(images)
    if not new_encodings:
        print("No encodings created. Make sure your face is clearly visible in the frame.")
        exit(0)

    known_encodings, known_names = load_existing_data()
    for enc in new_encodings:
        known_encodings.append(enc)
        known_names.append(person_name)

    save_data(known_encodings, known_names)
    print(f"[INFO] Registration done for {person_name}.")