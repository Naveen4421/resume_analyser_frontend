import sqlite3

conn = sqlite3.connect("resumes.db")
cursor = conn.cursor()

# Add score column
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN score REAL")
    print("✅ score column added to resumes table.")
except sqlite3.OperationalError:
    print("⚠ score column already exists.")

# Add feedback column
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN feedback TEXT")
    print("✅ feedback column added to resumes table.")
except sqlite3.OperationalError:
    print("⚠ feedback column already exists.")

conn.commit()
conn.close()

