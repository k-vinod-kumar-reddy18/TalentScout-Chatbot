"""
TalentScout Hiring Assistant
"""

import streamlit as st
from groq import Groq
import os
import sqlite3
from pypdf import PdfReader
import docx

# ── PAGE CONFIG ─────────────────────────────────────────────
st.set_page_config(
    page_title="TalentScout — Hiring Assistant",
    page_icon="🎯",
    layout="centered",
)

# ── LOAD API KEY ────────────────────────────────────────────
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("❌ GROQ_API_KEY not found in Streamlit Secrets")
    st.stop()

# ── INIT CLIENT ─────────────────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = Groq(api_key=api_key)

# ── SYSTEM PROMPT ───────────────────────────────────────────
SYSTEM_PROMPT = """
You are a professional Hiring Assistant for TalentScout.
Conduct structured candidate screening step by step.
Ask one question at a time.
"""

EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop"}

# ── DATABASE ────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("candidates.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

# ── RESUME PROCESSING ───────────────────────────────────────
def extract_text(file):
    text = ""

    if file.name.endswith(".pdf"):
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif file.name.endswith(".docx"):
        doc = docx.Document(file)
        for para in doc.paragraphs:
            text += para.text + "\n"

    return text.lower()

SKILLS = [
    "python", "java", "c++", "sql", "machine learning",
    "deep learning", "nlp", "flask", "django",
    "react", "node", "pandas", "numpy"
]

def extract_skills(text):
    return list(set([s for s in SKILLS if s in text]))

def calculate_score(skills):
    return min(len(skills) * 10, 100)

def save_candidate(name, email, phone, skills, score):
    conn = sqlite3.connect("candidates.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO candidates (name, email, phone, skills, score)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, phone, ", ".join(skills), score))
    conn.commit()
    conn.close()

# ── SESSION STATE ───────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

if "ended" not in st.session_state:
    st.session_state.ended = False

# ── CHAT FUNCTION ───────────────────────────────────────────
def call_groq(user_text):
    try:
        st.session_state.messages.append({
            "role": "user",
            "content": str(user_text)
        })

        completion = st.session_state.client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + [
                {"role": m["role"], "content": str(m["content"])}
                for m in st.session_state.messages
            ],
            temperature=0.7,
            max_tokens=500,
        )

        reply = completion.choices[0].message.content.strip()

        st.session_state.messages.append({
            "role": "assistant",
            "content": reply
        })

        return reply

    except Exception as e:
        return f"❌ Error: {e}"

# ── UI ──────────────────────────────────────────────────────
st.title("🎯 TalentScout Hiring Assistant")
st.caption("Powered by Groq (LLaMA 3)")

# ── RESUME UPLOAD ───────────────────────────────────────────
st.subheader("📄 Upload Resume")

file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])

if file:
    text = extract_text(file)
    skills = extract_skills(text)
    score = calculate_score(skills)

    st.success("Resume processed!")

    st.write("### Skills:")
    st.write(skills if skills else "No skills found")

    st.write("### Score:")
    st.progress(score / 100)
    st.write(f"{score}/100")

    if st.button("Save Candidate"):
        save_candidate("Unknown", "N/A", "N/A", skills, score)
        st.success("Saved!")

# ── CHAT DISPLAY ────────────────────────────────────────────
st.subheader("💬 Chat")

for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if not st.session_state.display_messages:
    opening = call_groq("Hello, I am a candidate starting my screening.")
    st.session_state.display_messages.append({"role": "assistant", "content": opening})

if user_input := st.chat_input("Type your message..."):
    st.session_state.display_messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        reply = call_groq(user_input)

    st.session_state.display_messages.append({"role": "assistant", "content": reply})

# ── SHOW DATABASE ───────────────────────────────────────────
if st.checkbox("📋 Show Saved Candidates"):
    conn = sqlite3.connect("candidates.db")
    rows = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()

    for r in rows:
        st.write(r)






