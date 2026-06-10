import sqlite3

# Create / connect to database file
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

# Create table (date + stdid = unique row)
cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    date TEXT,
    stdid TEXT,

    period1 INTEGER DEFAULT 0,
    period2 INTEGER DEFAULT 0,
    period3 INTEGER DEFAULT 0,
    period4 INTEGER DEFAULT 0,
    period5 INTEGER DEFAULT 0,
    period6 INTEGER DEFAULT 0,
    period7 INTEGER DEFAULT 0,
    period8 INTEGER DEFAULT 0,
    period9 INTEGER DEFAULT 0,
    period10 INTEGER DEFAULT 0,
    period11 INTEGER DEFAULT 0,
    period12 INTEGER DEFAULT 0,

    PRIMARY KEY (date, stdid)
)
""")

conn.commit()
conn.close()

print("Database and table created successfully!")
