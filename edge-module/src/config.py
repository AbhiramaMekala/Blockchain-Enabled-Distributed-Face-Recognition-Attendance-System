import os

# ================= CAMERA CONFIG =================

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

# Camera source (Jetson GStreamer)
CAMERA_INDEX = camSet

# Face recognition tolerance
TOLERANCE = 0.5

# ================= PATH CONFIG =================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
WEB_DIR = os.path.join(BASE_DIR, "web")

ENCODINGS_FILE = os.path.join(DATA_DIR, "encodings.npy")
NAMES_FILE = os.path.join(DATA_DIR, "names.npy")

# (Old single file not used anymore, but keeping for compatibility)
ATTENDANCE_FILE = os.path.join(LOGS_DIR, "attendance.csv")

# ================= TIMETABLE CONFIG =================

# Attendance allowed only in first N minutes of each period
ATTENDANCE_WINDOW_MIN = 20   # You can change this anytime

# Define your periods here (start_time, end_time)
# Format: ("HH:MM", "HH:MM")
# You can change, add, remove periods freely
PERIOD_TIMINGS = [
    ("09:00", "10:00"),
    ("10:00", "11:00"),
    ("11:00", "12:00"),
    ("12:00", "13:00"),
    ("13:00", "14:00"),
    ("14:00", "15:00"),
    ("15:00", "16:00"),
    ("16:00", "17:00"),
    ("17:00", "18:00"),
    ("18:00", "19:00"),
    ("19:00", "20:00"),
    ("20:00", "21:00"),
]

# ================= SYSTEM CONFIG =================

# How often to run face recognition (seconds)
PROCESS_EVERY_SECONDS = 5
