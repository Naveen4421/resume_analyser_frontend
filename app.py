import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

BASE_URL = "http://127.0.0.1:8000"

# -------------------------
# Session State Defaults
# -------------------------
for key, val in {"page":1, "logged_in":False, "token":None, "role":None, "username":None}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# -------------------------
# API Helpers
# -------------------------
def register(username, password, role):
    resp = requests.post(f"{BASE_URL}/register", json={"username": username, "password": password, "role": role})
    return resp.json()

def login(username, password, role):
    resp = requests.post(f"{BASE_URL}/login", json={"username": username, "password": password, "role": role})
    return resp.json()

def upload_job(title, description):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.post(f"{BASE_URL}/upload_job", json={"title": title, "description": description}, headers=headers)
    return resp.json()

def upload_resume(file, job_title="", job_description=""):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    files = {"file": (file.name, file, file.type)}
    data = {"job_title": job_title, "job_description": job_description}
    resp = requests.post(f"{BASE_URL}/upload_resume", headers=headers, files=files, data=data)
    return resp.json()

def match_resumes(job_id):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    resp = requests.get(f"{BASE_URL}/match_resumes/{job_id}", headers=headers)
    return resp.json()

# -------------------------
# Navigation Helpers
# -------------------------
def logout():
    for key in ["page","logged_in","token","role","username"]:
        st.session_state[key] = None if key != "page" else 1

def back():
    st.session_state.page = max(1, st.session_state.page - 1)

# -------------------------
# Pages
# -------------------------
st.title("🚀 Resume Matcher System")

# --------- PAGE 1: Login/Register ----------
if st.session_state.page == 1:
    st.header("Welcome! Please Login or Create Account")
    tab = st.tabs(["Login", "Register"])

    with tab[0]:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        role = st.selectbox("Role", ["applicant", "recruiter"], key="login_role")
        if st.button("Login"):
            resp = login(username, password, role)
            if "token" in resp:
                st.session_state.logged_in = True
                st.session_state.token = resp["token"]
                st.session_state.role = role
                st.session_state.username = username
                st.session_state.page = 2
            else:
                st.error(resp.get("detail", "Login failed"))

    with tab[1]:
        st.subheader("Register")
        reg_user = st.text_input("Username", key="reg_user")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        reg_role = st.selectbox("Role", ["applicant", "recruiter"], key="reg_role")
        if st.button("Register"):
            resp = register(reg_user, reg_pass, reg_role)
            if resp.get("msg"):
                st.success(resp["msg"])
            else:
                st.error(resp.get("detail", "Registration failed"))

# --------- PAGE 2: Role Selection ----------
elif st.session_state.page == 2:
    st.subheader(f"Hello, {st.session_state.username}!")
    st.button("Logout", on_click=logout)
    st.write("Select your role to continue:")

    # Animated buttons CSS
    st.markdown("""
    <style>
    .role-container {
        display: flex;
        justify-content: center;
        gap: 50px;
        margin-top: 50px;
    }
    .role-button {
        width: 250px;
        height: 150px;
        font-size: 36px;
        font-weight: bold;
        color: white;
        text-align: center;
        border-radius: 20px;
        cursor: pointer;
        transition: transform 0.3s, box-shadow 0.3s;
        display: flex;
        justify-content: center;
        align-items: center;
        position: relative;
        overflow: hidden;
    }
    .role-button:hover {
        transform: scale(1.15);
        box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }
    .applicant { background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); animation: pulse 2s infinite; }
    .recruiter { background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%); animation: pulse 2s infinite; }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 rgba(0,0,0,0.2); }
        50% { box-shadow: 0 0 25px rgba(0,0,0,0.4); }
        100% { box-shadow: 0 0 0 rgba(0,0,0,0.2); }
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="role-button applicant">Applicant</div>', unsafe_allow_html=True)
        if st.button("Select Applicant", key="applicant_btn"):
            st.session_state.page = 3
            st.session_state.role = "applicant"
    with col2:
        st.markdown('<div class="role-button recruiter">Recruiter</div>', unsafe_allow_html=True)
        if st.button("Select Recruiter", key="recruiter_btn"):
            st.session_state.page = 3
            st.session_state.role = "recruiter"

    st.button("Back", on_click=back)

# --------- PAGE 3: Role-specific ----------
elif st.session_state.page == 3:
    st.button("Logout", on_click=logout)
    st.button("Back", on_click=back)

    # ---------- Applicant Portal ----------
    if st.session_state.role == "applicant":
        st.header("Applicant Portal")
        uploaded_file = st.file_uploader("Upload your resume", type=["pdf","docx","xlsx","csv","py","js","java","cpp","png","jpg"])
        job_title = st.text_input("Job Title (optional)")
        job_desc = st.text_area("Job Description (optional)")
        if uploaded_file and st.button("Submit Resume"):
            resp = upload_resume(uploaded_file, job_title, job_desc)
            if "resume_id" in resp:
                st.success("✅ Resume uploaded successfully!")
                score = resp.get('score',0)
                st.write(f"**Score:** {score*100:.1f}%")
                st.write(f"**Feedback:** {resp.get('feedback')}")
                # Pie chart
                fig, ax = plt.subplots()
                ax.pie([score, 1-score], labels=["Match","Missing"], autopct="%1.1f%%", colors=["#4caf50","#f44336"])
                ax.set_title("ATS Matching Score")
                st.pyplot(fig)
            else:
                st.error("❌ Error uploading resume.")

    # ---------- Recruiter Portal ----------
    elif st.session_state.role == "recruiter":
        st.header("Recruiter Portal")

        # Upload Job
        st.subheader("Upload Job")
        job_title = st.text_input("Job Title", key="job_title_recruiter")
        job_desc = st.text_area("Job Description", key="job_desc_recruiter")
        if st.button("Upload Job", key="upload_job_btn"):
            resp = upload_job(job_title, job_desc)
            if "job_id" in resp:
                st.success(f"Job uploaded with ID: {resp.get('job_id')}")
            else:
                st.error("Failed to upload job")

        # Upload Applicant Resume
        st.subheader("Upload Applicant Resume")
        uploaded_file = st.file_uploader(
            "Upload Resume", 
            type=["pdf","docx","xlsx","csv","py","js","java","cpp","png","jpg"],
            key="recruiter_upload"
        )
        job_title2 = st.text_input("Job Title for Resume Match", key="job_title_resume")
        job_desc2 = st.text_area("Job Description for Resume Match", key="job_desc_resume")
        if uploaded_file and st.button("Submit Applicant Resume", key="submit_resume_btn"):
            resp = upload_resume(uploaded_file, job_title2, job_desc2)
            if "resume_id" in resp:
                st.success("✅ Resume uploaded successfully!")
                score = resp.get('score',0)
                st.write(f"**Score:** {score*100:.1f}%")
                st.write(f"**Feedback:** {resp.get('feedback')}")
                # Pie chart
                fig, ax = plt.subplots()
                ax.pie([score, 1-score], labels=["Match","Missing"], autopct="%1.1f%%", colors=["#4caf50","#f44336"])
                ax.set_title("ATS Matching Score")
                st.pyplot(fig)
            else:
                st.error("❌ Error uploading resume.")

        # Match Resumes & Summary
        st.subheader("Match Resumes & Summary")
        job_id_input = st.number_input("Enter Job ID to Match Resumes", min_value=1, step=1, key="match_job_id")
        if st.button("Match Resumes", key="match_resumes_btn"):
            resp = match_resumes(job_id_input)
            if "matches" in resp:
                df = pd.DataFrame(resp["matches"])[["filename","user_id","score","feedback","ranking","status"]]
                df["score"] = df["score"]*100

                # Summary stats
                total = len(df)
                shortlisted = len(df[df["status"]=="Shortlisted"])
                not_eligible = len(df[df["status"]=="Not Eligible"])
                st.write(f"**Total Applications:** {total}")
                st.write(f"**Shortlisted:** {shortlisted}")
                st.write(f"**Not Eligible:** {not_eligible}")

                # Detailed table
                st.table(df)

                # ---------- Charts ----------
                st.subheader("Visualization")
                # Pie chart
                fig, ax = plt.subplots()
                ax.pie([shortlisted, not_eligible], labels=["Shortlisted","Not Eligible"], autopct="%1.1f%%", colors=["#4caf50","#f44336"])
                ax.set_title("Shortlist vs Not Eligible")
                st.pyplot(fig)

                # Bar chart - Score distribution
                fig, ax = plt.subplots()
                x = range(len(df))
                ax.bar(x, df["score"], color="#2196f3")
                ax.set_xticks(x)
                ax.set_xticklabels(df["filename"], rotation=45, ha="right")
                ax.set_ylabel("Score (%)")
                ax.set_title("Resume Score Distribution")
                st.pyplot(fig)
            else:
                st.error(resp.get("detail", "No matches found"))

