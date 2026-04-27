"""
TalentScout Hiring Assistant

"""

import streamlit as st
import anthropic
import os
import json
import re
from datetime import datetime

# ─────────────────────────── PAGE CONFIG ──────────────────────────────
st.set_page_config(
    page_title="TalentScout | Hiring Assistant",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────── CUSTOM CSS ───────────────────────────────
st.markdown("""
<style>
    /* Main container */
    .stApp { background-color: #0f1117; color: #e0e0e0; }

    /* Title */
    h1 { color: #4fc3f7 !important; }
    h2, h3 { color: #81d4fa !important; }

    /* Progress bar */
    .stProgress > div > div { background-color: #4fc3f7; }

    /* Chat messages */
    .stChatMessage { border-radius: 12px; margin: 4px 0; }

    /* Metric cards */
    .stMetric { background: #1e2130; border-radius: 10px; padding: 10px; }

    /* Info box */
    .info-box {
        background: #1a2744;
        border-left: 4px solid #4fc3f7;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-size: 0.9rem;
    }

    /* Stage badge */
    .stage-badge {
        display: inline-block;
        background: #1565c0;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── API KEY ──────────────────────────────────
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    st.error("⚠️ ANTHROPIC_API_KEY not set. Please set the environment variable.")
    st.stop()

client = anthropic.Anthropic(api_key=api_key)

# ─────────────────────────── CONSTANTS ────────────────────────────────
EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "stop", "end", "cancel"}

STAGES = [
    "Greeting",
    "Contact Info",
    "Professional Background",
    "Tech Stack",
    "Technical Assessment",
    "Closing",
]

# ─────────────────────────── SYSTEM PROMPT ────────────────────────────
SYSTEM_PROMPT = """You are TalentScout's AI Hiring Assistant — a professional, warm, and concise recruiter chatbot for a technology recruitment agency.

## Your Goal
Conduct a structured initial screening of technology candidates by collecting their information and assessing their technical skills.

## Conversation Stages (follow in strict order)

### STAGE 1 — Greeting
- Warmly welcome the candidate
- Briefly explain that you will collect their details and ask some technical questions
- Ask for their full name to begin

### STAGE 2 — Contact & Personal Info (collect one at a time)
Collect in order:
1. Email address
2. Phone number
3. Current location (city, country)

### STAGE 3 — Professional Background (collect one at a time)
Collect in order:
1. Years of professional experience
2. Desired role/position they are applying for

### STAGE 4 — Tech Stack Declaration
- Ask the candidate to list ALL technologies they are proficient in: programming languages, frameworks, libraries, databases, cloud tools, etc.
- Encourage them to be thorough

### STAGE 5 — Technical Assessment
- Based on the declared tech stack, generate exactly 3–5 technical questions
- Questions must be:
  - Directly mapped to the specific technologies the candidate mentioned
  - Intermediate level (not trivial, not PhD-level)
  - Varied: mix conceptual, practical, and problem-solving
- Ask ONE question at a time
- After each answer, briefly acknowledge it (1 sentence) then proceed to the next question
- Do NOT give feedback on whether the answer is correct

### STAGE 6 — Closing
- Thank the candidate warmly
- Inform them that their responses have been recorded
- Tell them a recruiter will be in touch within 3–5 business days
- Wish them well

## Strict Rules
- Ask ONLY ONE question per turn — never combine or bundle questions
- Never re-ask information already provided in the conversation
- Stay strictly on-topic; if the user asks something unrelated, politely redirect: "I'm here to assist with your screening — let's continue!"
- If you don't understand a response, ask for clarification once, then move on
- Keep responses concise: 1–3 sentences unless generating technical questions
- Be friendly and encouraging throughout
- When generating technical questions, number them clearly and only ask the first one initially

## Conversation End Detection
If the candidate says goodbye, thanks for the chat, wants to stop, or uses any closing language, gracefully conclude the conversation even if all stages are not complete.

## JSON Summary (internal use)
After the closing, append a hidden JSON block at the very end of your final message in this exact format (do not show it unless explicitly in the closing stage):
<candidate_data>
{
  "name": "...",
  "email": "...",
  "phone": "...",
  "location": "...",
  "experience_years": "...",
  "desired_role": "...",
  "tech_stack": ["...", "..."],
  "screening_date": "YYYY-MM-DD"
}
</candidate_data>
"""

# ─────────────────────────── SESSION STATE ────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []          # sent to API
if "display" not in st.session_state:
    st.session_state.display = []           # shown in UI
if "stage_index" not in st.session_state:
    st.session_state.stage_index = 0
if "ended" not in st.session_state:
    st.session_state.ended = False
if "candidate_summary" not in st.session_state:
    st.session_state.candidate_summary = {}
if "initialized" not in st.session_state:
    st.session_state.initialized = False

# ─────────────────────────── HELPERS ──────────────────────────────────

def detect_stage(text: str) -> int:
    """Heuristic to estimate which stage we're in based on assistant text."""
    text_lower = text.lower()
    if any(k in text_lower for k in ["thank you", "recruiter will", "best of luck", "all the best"]):
        return 5
    if any(k in text_lower for k in ["question", "tell me about", "explain", "what is", "how would"]):
        return 4
    if any(k in text_lower for k in ["tech stack", "technologies", "programming language", "frameworks"]):
        return 3
    if any(k in text_lower for k in ["experience", "years", "desired role", "applying for"]):
        return 2
    if any(k in text_lower for k in ["email", "phone", "location", "city"]):
        return 1
    return st.session_state.stage_index

def is_exit(text: str) -> bool:
    """Check if user wants to exit."""
    return any(kw in text.lower().split() for kw in EXIT_KEYWORDS)

def extract_candidate_data(text: str) -> dict:
    """Extract the hidden JSON summary from the closing message."""
    match = re.search(r"<candidate_data>(.*?)</candidate_data>", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    return {}

def clean_display_text(text: str) -> str:
    """Remove the hidden JSON block from display text."""
    return re.sub(r"<candidate_data>.*?</candidate_data>", "", text, flags=re.DOTALL).strip()

def call_ai(user_input: str) -> str:
    """Send message to Claude and return response."""
    st.session_state.messages.append({"role": "user", "content": user_input})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=st.session_state.messages,
    )

    reply = response.content[0].text
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Extract candidate data if present
    data = extract_candidate_data(reply)
    if data:
        st.session_state.candidate_summary = data

    # Update stage
    st.session_state.stage_index = detect_stage(reply)

    return clean_display_text(reply)

# ─────────────────────────── SIDEBAR ──────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Screening Progress")
    progress = (st.session_state.stage_index + 1) / len(STAGES)
    st.progress(min(progress, 1.0))
    st.markdown(f"**Stage {st.session_state.stage_index + 1} of {len(STAGES)}:** {STAGES[st.session_state.stage_index]}")

    st.divider()
    st.markdown("### 🗂️ Stages")
    for i, s in enumerate(STAGES):
        icon = "✅" if i < st.session_state.stage_index else ("🔵" if i == st.session_state.stage_index else "⬜")
        st.markdown(f"{icon} {s}")

    st.divider()
    if st.button("🔄 Start New Screening", use_container_width=True):
        for key in ["messages", "display", "stage_index", "ended", "candidate_summary", "initialized"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    if st.session_state.candidate_summary:
        st.divider()
        st.markdown("### 📋 Candidate Profile")
        s = st.session_state.candidate_summary
        for label, key in [("Name", "name"), ("Email", "email"), ("Location", "location"),
                            ("Experience", "experience_years"), ("Role", "desired_role")]:
            if s.get(key):
                st.markdown(f"**{label}:** {s[key]}")
        if s.get("tech_stack"):
            st.markdown(f"**Stack:** {', '.join(s['tech_stack'])}")

# ─────────────────────────── HEADER ───────────────────────────────────
st.markdown("# 🎯 TalentScout Hiring Assistant")
st.markdown(
    '<div class="info-box">👋 Welcome! I\'m your AI screening assistant. '
    'This session collects your profile and assesses your technical skills. '
    'Type <b>exit</b> at any time to end the session.</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────── INIT CHAT ────────────────────────────────
if not st.session_state.initialized:
    with st.spinner("Starting your screening session…"):
        opening = call_ai("Begin the candidate screening. Greet the candidate and ask for their full name.")
    st.session_state.display.append(("assistant", opening))
    st.session_state.initialized = True

# ─────────────────────────── CHAT DISPLAY ─────────────────────────────
for role, msg in st.session_state.display:
    with st.chat_message(role, avatar="🤖" if role == "assistant" else "👤"):
        st.markdown(msg)

# ─────────────────────────── USER INPUT ───────────────────────────────
if not st.session_state.ended:
    user_input = st.chat_input("Type your response here…")

    if user_input:
        # Display user message
        st.session_state.display.append(("user", user_input))

        # Check for exit keywords
        if is_exit(user_input):
            farewell = (
                "Thank you for your time today! 🎉 Your responses have been noted, "
                "and a member of our recruitment team will be in touch with you shortly. "
                "Best of luck with your application — have a great day!"
            )
            st.session_state.display.append(("assistant", farewell))
            st.session_state.stage_index = 5
            st.session_state.ended = True
        else:
            with st.spinner("Thinking…"):
                reply = call_ai(user_input)
            st.session_state.display.append(("assistant", reply))

            # Detect if conversation is naturally ended
            if any(phrase in reply.lower() for phrase in
                   ["recruiter will be in touch", "best of luck", "screening is complete",
                    "we'll be in touch", "goodbye", "take care"]):
                st.session_state.ended = True

        st.rerun()
else:
    st.success("✅ Screening session completed! A recruiter will reach out within 3–5 business days.")
    if st.button("🔄 Start a New Screening", use_container_width=True):
        for key in ["messages", "display", "stage_index", "ended", "candidate_summary", "initialized"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
