import sqlite3

conn = sqlite3.connect("resumes.db")
cursor = conn.cursor()

# Add user_id column if it doesn't exist
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN user_id INTEGER")
    print("✅ user_id column added to resumes table.")
except sqlite3.OperationalError:
    print("⚠ user_id column already exists.")

# Add status column if it doesn't exist
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN status TEXT DEFAULT 'Pending'")
    print("✅ status column added to resumes table.")
except sqlite3.OperationalError:
    print("⚠ status column already exists.")

# Add ranking column if it doesn't exist
try:
    cursor.execute("ALTER TABLE resumes ADD COLUMN ranking INTEGER DEFAULT 0")
    print("✅ ranking column added to resumes table.")
except sqlite3.OperationalError:
    print("⚠ ranking column already exists.")

conn.commit()
conn.close()
print("✅ Database update complete.")

