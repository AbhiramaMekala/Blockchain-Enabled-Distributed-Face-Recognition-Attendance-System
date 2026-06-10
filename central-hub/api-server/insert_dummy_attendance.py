import sqlite3

def insert_dummy_data():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()

    dummy_data = [
        ("2026-02-12", "101", 1,1,1,1,1,1,1,1,1,1,1,1),
        ("2026-02-12", "102", 1,0,1,1,0,1,1,1,0,1,1,1),
        ("2026-02-12", "103", 0,0,1,1,1,0,1,1,1,1,1,0),
        ("2026-02-13", "101", 1,1,1,1,1,1,1,1,1,1,1,1),
        ("2026-02-13", "102", 1,1,0,0,1,1,1,0,1,1,1,1),
    ]

    cursor.executemany("""
    INSERT OR REPLACE INTO attendance (
        date, stdid,
        period1, period2, period3, period4,
        period5, period6, period7, period8,
        period9, period10, period11, period12
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, dummy_data)

    conn.commit()
    conn.close()

    print("Dummy data inserted successfully!")

if __name__ == "__main__":
    insert_dummy_data()
