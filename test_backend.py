import requests

BASE_URL = "http://127.0.0.1:8000"

# --------------------------
# 1️⃣ Register users
# --------------------------
users = [
    {"username": "applicant1", "password": "pass123", "role": "applicant"},
    {"username": "recruiter1", "password": "pass123", "role": "recruiter"}
]

for u in users:
    resp = requests.post(f"{BASE_URL}/register", json=u)
    print("Register:", resp.json())

# --------------------------
# 2️⃣ Login (get token)
# --------------------------
login_data = {"username": "recruiter1", "password": "pass123"}
resp = requests.post(f"{BASE_URL}/login", data=login_data)
token = resp.json().get("access_token")
print("Login:", resp.json())

headers = {"Authorization": f"Bearer {token}"}

# --------------------------
# 3️⃣ Upload a job (recruiter)
# --------------------------
job = {"title": "Software Engineer", "description": "Python, FastAPI, AI"}
resp = requests.post(f"{BASE_URL}/jobs", headers=headers, json=job)
print("Upload Job:", resp.json())
job_id = resp.json().get("job_id")

# --------------------------
# 4️⃣ Upload a resume (applicant)
# --------------------------
files = {"file": open("/home/naveen/Downloads/resume - 1.pdf", "rb")}
applicant_login = {"username": "applicant1", "password": "pass123"}
resp = requests.post(f"{BASE_URL}/login", data=applicant_login)
applicant_token = resp.json().get("access_token")
applicant_headers = {"Authorization": f"Bearer {applicant_token}"}

resp = requests.post(f"{BASE_URL}/resumes", headers=applicant_headers, files=files)
print("Upload Resume:", resp.json())

# --------------------------
# 5️⃣ Match resumes for job (recruiter)
# --------------------------
resp = requests.get(f"{BASE_URL}/match/{job_id}", headers=headers)
print("Match Resumes:", resp.json())

