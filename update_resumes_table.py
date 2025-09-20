import sqlite3

conn = sqlite3.connect("resumes.db")
cursor = conn.cursor()

# Add file_type column if it doesn't exist
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN file_type TEXT")
    print("✅ 'file_type' column added")
except sqlite3.OperationalError:
    print("⚠ 'file_type' column already exists")

# Add status column if it doesn't exist
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN status TEXT")
    print("✅ 'status' column added")
except sqlite3.OperationalError:
    print("⚠ 'status' column already exists")

# Add ranking column if it doesn't exist
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN ranking INTEGER")
    print("✅ 'ranking' column added")
except sqlite3.OperationalError:
    print("⚠ 'ranking' column already exists")

conn.commit()
conn.close()

