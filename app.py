"""
TalentScout Hiring Assistant (Final Assignment Version)
"""

import streamlit as st
from groq import Groq
import os
import sqlite3
import re
from pypdf import PdfReader
import docx

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="🎯")

# ---------------- API KEY ----------------
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("API key missing")
    st.stop()

client = Groq(api_key=api_key)

# ---------------- SYSTEM PROMPT ----------------
SYSTEM_PROMPT = """
You are a Hiring Assistant chatbot.

Follow steps strictly:
1. Ask full name
2. Ask email
3. Ask phone
4. Ask experience
5. Ask desired role
6. Ask location
7. Ask tech stack
8. Generate 3-5 technical questions based on tech stack
9. Ask questions one by one
10. End conversation politely

Rules:
- Ask ONE question at a time
- Be concise
"""

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("candidates.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,
        score INTEGER
    )
    """)
    conn.commit()
    conn.close()

init_db()

def save_candidate(name, email, phone, skills, score):
    conn = sqlite3.connect("candidates.db")
    c = conn.cursor()
    c.execute("INSERT INTO candidates VALUES (NULL,?,?,?,?,?)",
              (name, email, phone, skills, score))
    conn.commit()
    conn.close()

# ---------------- RESUME PROCESS ----------------
def extract_text(file):
    text = ""
    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for p in doc.paragraphs:
            text += p.text
    return text.lower()

SKILLS = ["python","java","sql","machine learning","deep learning",
          "nlp","flask","django","react","node","pandas","numpy"]

def extract_skills(text):
    text = re.sub(r'[^a-zA-Z ]', ' ', text)
    return list(set([s for s in SKILLS if s in text]))

def calculate_score(skills):
    return min(len(skills)*15,100)

def extract_email(text):
    match = re.search(r"\S+@\S+", text)
    return match.group(0) if match else "Not found"

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "display" not in st.session_state:
    st.session_state.display = []

# ---------------- CHAT FUNCTION ----------------
def call_ai(user_input):
    st.session_state.messages.append({"role":"user","content":user_input})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT}
        ] + st.session_state.messages,
        temperature=0.7
    )

    reply = response.choices[0].message.content
    st.session_state.messages.append({"role":"assistant","content":reply})
    return reply

# ---------------- UI ----------------
st.title("🎯 TalentScout Hiring Assistant")

# ---------- Resume Upload ----------
st.subheader("📄 Upload Resume")

file = st.file_uploader("Upload PDF/DOCX", type=["pdf","docx"])

if file:
    text = extract_text(file)
    skills = extract_skills(text)
    score = calculate_score(skills)
    email = extract_email(text)

    st.success("Resume Processed!")

    st.write("📧 Email:", email)
    st.write("🧠 Skills:", skills if skills else "No skills found")

    st.progress(score/100)
    st.write(f"Score: {score}/100")

    if st.button("Save Candidate"):
        save_candidate("Unknown", email, "N/A", ", ".join(skills), score)
        st.success("Saved!")

# ---------- Chat ----------
st.subheader("💬 Chat")

if not st.session_state.display:
    opening = call_ai("Start screening")
    st.session_state.display.append(("assistant", opening))

for role, msg in st.session_state.display:
    with st.chat_message(role):
        st.write(msg)

user_input = st.chat_input("Type your answer...")

if user_input:
    st.session_state.display.append(("user", user_input))

    reply = call_ai(user_input)
    st.session_state.display.append(("assistant", reply))

    st.rerun()

# ---------- Show DB ----------
if st.checkbox("📋 Show Candidates"):
    conn = sqlite3.connect("candidates.db")
    data = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()

    for row in data:
        st.write(row)
        


