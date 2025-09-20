from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
import sqlite3
import os
import fitz  # PyMuPDF
import docx2txt
import pandas as pd
from io import BytesIO
import re
from typing import List

app = FastAPI()
DB_FILE = "resumes.db"
SECRET_KEY = "secretkey123"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# -------------------------
# Database Setup
# -------------------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

# Users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")
# Resumes
cursor.execute("""
CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    file_type TEXT,
    content TEXT,
    user_id INTEGER,
    score REAL,
    feedback TEXT,
    status TEXT,
    ranking INTEGER
)
""")
# Jobs
cursor.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT
)
""")
conn.commit()

# -------------------------
# Models
# -------------------------
class User(BaseModel):
    username: str
    password: str
    role: str

class Job(BaseModel):
    title: str
    description: str

# -------------------------
# Auth helpers
# -------------------------
def create_token(user_id: int):
    return jwt.encode({"user_id": user_id}, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# -------------------------
# File processing helpers
# -------------------------
def extract_text_from_pdf(file_bytes):
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.lower()

def extract_text_from_docx(file_bytes):
    with BytesIO(file_bytes) as f:
        text = docx2txt.process(f)
    return text.lower()

def extract_text_from_excel(file_bytes):
    df = pd.read_excel(BytesIO(file_bytes))
    return df.to_string().lower()

def extract_text_from_code(file_bytes):
    return file_bytes.decode("utf-8", errors="ignore").lower()

# -------------------------
# Keyword-based scoring
# -------------------------
def generate_score_and_feedback(resume_text: str, job_title: str, job_desc: str):
    # Extract keywords (words longer than 3 letters)
    job_keywords = set(re.findall(r"\b\w{4,}\b", job_title + " " + job_desc.lower()))
    resume_words = set(re.findall(r"\b\w{4,}\b", resume_text.lower()))
    
    if not job_keywords:
        return 0.0, "Job description too short for analysis."
    
    matched_keywords = job_keywords.intersection(resume_words)
    score = round(len(matched_keywords) / len(job_keywords), 2)  # percentage match
    
    # Generate feedback for missing keywords
    missing_keywords = job_keywords - matched_keywords
    if missing_keywords:
        feedback = "Your resume is missing these important keywords: " + ", ".join(list(missing_keywords)[:10])
    else:
        feedback = "Excellent! Your resume matches most of the job keywords."
    
    return score, feedback

# -------------------------
# User Endpoints
# -------------------------
@app.post("/register")
def register(user: User):
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       (user.username, user.password, user.role))
        conn.commit()
        return {"msg": "User registered successfully"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists")

@app.post("/login")
def login(user: User):
    cursor.execute("SELECT id FROM users WHERE username=? AND password=? AND role=?",
                   (user.username, user.password, user.role))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(row[0])
    return {"token": token}

# -------------------------
# Job Endpoints
# -------------------------
@app.post("/upload_job")
def upload_job(job: Job, token: str = Depends(oauth2_scheme)):
    user_id = decode_token(token)
    cursor.execute("INSERT INTO jobs (title, description) VALUES (?, ?)", (job.title, job.description))
    conn.commit()
    return {"job_id": cursor.lastrowid}

# -------------------------
# Resume Endpoints
# -------------------------
@app.post("/upload_resume")
def upload_resume(file: UploadFile = File(...), job_title: str = "", job_description: str = "", token: str = Depends(oauth2_scheme)):
    user_id = decode_token(token)
    file_bytes = file.file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext == ".pdf":
        content = extract_text_from_pdf(file_bytes)
    elif ext in [".docx"]:
        content = extract_text_from_docx(file_bytes)
    elif ext in [".xlsx", ".csv"]:
        content = extract_text_from_excel(file_bytes)
    elif ext in [".py", ".js", ".java", ".cpp"]:
        content = extract_text_from_code(file_bytes)
    elif ext in [".png", ".jpg", ".jpeg"]:
        content = ""  # Images stored but no text
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Generate realistic ATS score and feedback
    score, feedback = generate_score_and_feedback(content, job_title, job_description)
    
    # Determine status
    status = "Shortlisted" if score >= 0.5 else "Not Eligible"
    
    cursor.execute(
        "INSERT INTO resumes (filename, file_type, content, user_id, score, feedback, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (file.filename, ext, content, user_id, score, feedback, status)
    )
    conn.commit()
    return {"resume_id": cursor.lastrowid, "score": score, "feedback": feedback, "status": status, "preview": content[:200]}

# -------------------------
# Resume Matching
# -------------------------
@app.get("/match_resumes/{job_id}")
def match_resumes(job_id: int, token: str = Depends(oauth2_scheme)):
    user_id = decode_token(token)
    cursor.execute("SELECT title, description FROM jobs WHERE id=?", (job_id,))
    job_row = cursor.fetchone()
    if not job_row:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_title, job_desc = job_row
    cursor.execute("SELECT id, filename, content, user_id FROM resumes")
    resumes = cursor.fetchall()
    
    matches = []
    for idx, r in enumerate(resumes):
        score, feedback = generate_score_and_feedback(r[2], job_title, job_desc)
        status = "Shortlisted" if score >= 0.5 else "Not Eligible"
        matches.append({
            "resume_id": r[0],
            "filename": r[1],
            "user_id": r[3],
            "score": score,
            "feedback": feedback,
            "preview": r[2][:200],
            "ranking": idx + 1,
            "status": status
        })
        # Update database
        cursor.execute("UPDATE resumes SET score=?, feedback=?, status=?, ranking=? WHERE id=?",
                       (score, feedback, status, idx + 1, r[0]))
    conn.commit()
    
    return {"job_id": job_id, "matches": matches}

# -------------------------
# Resume Summary for Dashboard
# -------------------------
@app.get("/resume_summary")
def resume_summary(token: str = Depends(oauth2_scheme)):
    user_id = decode_token(token)
    cursor.execute("SELECT COUNT(*) FROM resumes")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resumes WHERE status='Shortlisted'")
    shortlisted = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM resumes WHERE status='Not Eligible'")
    not_eligible = cursor.fetchone()[0]
    
    return {
        "total_applications": total,
        "shortlisted": shortlisted,
        "not_eligible": not_eligible
    }

