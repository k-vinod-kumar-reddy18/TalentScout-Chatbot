"""
TalentScout — AI Hiring Assistant

"""

import streamlit as st
from groq import Groq
import os
import json
import re

# ─────────────────────────── PAGE CONFIG ──────────────────────────────
st.set_page_config(
    page_title="TalentScout | Hiring Assistant",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── CUSTOM CSS ───────────────────────────────
st.markdown("""
<style>
    /* Background */
    .stApp { background-color: #0f1117; color: #e0e0e0; }

    /* Headings */
    h1 { color: #4fc3f7 !important; text-align: center; }
    h2, h3 { color: #81d4fa !important; }

    /* Progress bar */
    .stProgress > div > div { background-color: #4fc3f7 !important; }

    /* Chat bubbles */
    .stChatMessage { border-radius: 12px; margin: 4px 0; }

    /* Info banner */
    .info-banner {
        background: #1a2744;
        border-left: 4px solid #4fc3f7;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        font-size: 0.88rem;
        margin-bottom: 16px;
    }

    /* Sidebar card */
    .profile-card {
        background: #1e2130;
        border-radius: 10px;
        padding: 10px 14px;
        font-size: 0.85rem;
        margin-top: 6px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────── API KEY ──────────────────────────────────
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ **GROQ_API_KEY** environment variable is not set. "
             "Please set it and restart the app.")
    st.code("export GROQ_API_KEY='your_key_here'", language="bash")
    st.stop()

client = Groq(api_key=api_key)

# ─────────────────────────── CONSTANTS ────────────────────────────────
MODEL        = "llama-3.1-8b-instant"
MAX_TOKENS   = 800
TEMPERATURE  = 0.7

EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "stop", "end", "cancel", "done"}

STAGES = [
    "👋 Greeting",
    "📇 Contact Info",
    "💼 Professional Background",
    "🛠️ Tech Stack",
    "🧠 Technical Assessment",
    "✅ Closing",
]

# ─────────────────────────── SYSTEM PROMPT ────────────────────────────
SYSTEM_PROMPT = """You are the TalentScout AI Hiring Assistant — a professional, friendly, and concise recruiter chatbot for a technology recruitment agency called TalentScout.

## YOUR MISSION
Conduct a structured initial screening of technology candidates by collecting their personal/professional details and assessing their technical knowledge through targeted questions.

## CONVERSATION STAGES — follow strictly in order

### STAGE 1 — Greeting
- Warmly welcome the candidate to TalentScout
- Briefly explain you will collect their details and ask a few technical questions
- Ask for their full name to get started

### STAGE 2 — Contact & Personal Info
Collect ONE at a time, in this order:
1. Email address
2. Phone number
3. Current location (city and country)

### STAGE 3 — Professional Background
Collect ONE at a time, in this order:
1. Years of professional experience
2. Desired role / position they are applying for

### STAGE 4 — Tech Stack Declaration
- Ask the candidate to list ALL technologies they are comfortable with:
  programming languages, frameworks, libraries, databases, cloud tools, DevOps, etc.
- Encourage them to be as thorough as possible

### STAGE 5 — Technical Assessment
- Based ONLY on the technologies the candidate declared, generate exactly 3–5 technical questions
- Question quality rules:
  - Directly mapped to the specific technologies mentioned — never generic
  - Intermediate difficulty (not trivial hello-world, not PhD research)
  - Mix of conceptual, practical, and problem-solving types
- Ask ONE question at a time
- After each answer, acknowledge briefly (1 short sentence) then ask the next question
- Do NOT say whether the answer is correct or incorrect

### STAGE 6 — Closing
- Thank the candidate warmly by name
- Tell them their responses have been recorded
- Inform them a recruiter will reach out within 3–5 business days
- Wish them well and say goodbye
- At the very end of your closing message, append this block (hidden from candidate):
<candidate_data>
{
  "name": "...",
  "email": "...",
  "phone": "...",
  "location": "...",
  "experience_years": "...",
  "desired_role": "...",
  "tech_stack": ["...", "..."]
}
</candidate_data>

## STRICT RULES
1. Ask ONLY ONE question per turn — never bundle or combine questions
2. Never re-ask information already provided in the conversation
3. Stay on-topic at all times — if the user asks something unrelated, reply:
   "I'm here to assist with your screening — let's continue! 😊"
4. If you don't understand a response, ask for clarification once, then move on
5. Keep all responses concise: 1–3 sentences maximum (except when generating technical questions)
6. Be warm, encouraging, and professional throughout
7. If the candidate says goodbye, thanks, or wants to stop → jump directly to Stage 6 closing

## FALLBACK
If the candidate sends anything completely unrelated (jokes, random text, profanity), respond:
"Let's keep things on track! I'm here to help with your TalentScout screening. Shall we continue?"
"""

# ─────────────────────────── SESSION STATE ────────────────────────────
defaults = {
    "messages":          [],      # full history sent to API
    "display":           [],      # (role, text) pairs shown in UI
    "stage_index":       0,       # current stage 0-5
    "ended":             False,   # has conversation finished
    "candidate_summary": {},      # extracted JSON profile
    "initialized":       False,   # has greeting been sent
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────── HELPER FUNCTIONS ─────────────────────────

def is_exit(text: str) -> bool:
    """Return True if the user typed an exit keyword."""
    words = set(re.sub(r"[^a-z ]", "", text.lower()).split())
    return bool(words & EXIT_KEYWORDS)


def detect_stage(text: str) -> int:
    """Heuristically update stage index from assistant reply."""
    t = text.lower()
    if any(k in t for k in ["recruiter will", "best of luck", "all the best", "goodbye", "take care"]):
        return 5
    if any(k in t for k in ["question", "explain", "how would you", "what is", "describe", "difference between"]):
        return 4
    if any(k in t for k in ["tech stack", "technologies", "programming language", "frameworks", "tools you"]):
        return 3
    if any(k in t for k in ["years of experience", "desired role", "position", "applying for"]):
        return 2
    if any(k in t for k in ["email", "phone", "location", "city", "contact"]):
        return 1
    return st.session_state.stage_index


def extract_candidate_data(text: str) -> dict:
    """Pull the hidden JSON block from the closing message."""
    match = re.search(r"<candidate_data>(.*?)</candidate_data>", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


def clean_text(text: str) -> str:
    """Strip the hidden JSON block before displaying."""
    return re.sub(r"<candidate_data>.*?</candidate_data>", "", text, flags=re.DOTALL).strip()


def call_ai(user_input: str) -> str:
    """Append user message, call Groq, return cleaned assistant reply."""
    st.session_state.messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                 + st.session_state.messages,
    )

    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Extract candidate profile if present (closing stage)
    data = extract_candidate_data(reply)
    if data:
        st.session_state.candidate_summary = data

    # Update stage tracker
    st.session_state.stage_index = detect_stage(reply)

    return clean_text(reply)

# ─────────────────────────── SIDEBAR ──────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Screening Progress")

    progress = (st.session_state.stage_index + 1) / len(STAGES)
    st.progress(min(progress, 1.0))
    st.caption(f"Stage {st.session_state.stage_index + 1} of {len(STAGES)}: "
               f"**{STAGES[st.session_state.stage_index]}**")

    st.divider()
    st.markdown("### 🗂️ All Stages")
    for i, stage in enumerate(STAGES):
        if i < st.session_state.stage_index:
            icon = "✅"
        elif i == st.session_state.stage_index:
            icon = "🔵"
        else:
            icon = "⬜"
        st.markdown(f"{icon} {stage}")

    st.divider()
    if st.button("🔄 Start New Screening", use_container_width=True):
        for k in list(defaults.keys()):
            st.session_state[k] = defaults[k]
        st.rerun()

    # Show extracted candidate profile once available
    if st.session_state.candidate_summary:
        st.divider()
        st.markdown("### 📋 Candidate Profile")
        s = st.session_state.candidate_summary
        fields = [
            ("Name",       "name"),
            ("Email",      "email"),
            ("Phone",      "phone"),
            ("Location",   "location"),
            ("Experience", "experience_years"),
            ("Role",       "desired_role"),
        ]
        for label, key in fields:
            if s.get(key):
                st.markdown(f"**{label}:** {s[key]}")
        if s.get("tech_stack"):
            stack = s["tech_stack"]
            if isinstance(stack, list):
                stack = ", ".join(stack)
            st.markdown(f"**Tech Stack:** {stack}")

# ─────────────────────────── MAIN HEADER ──────────────────────────────
st.markdown("# 🎯 TalentScout Hiring Assistant")
st.markdown(
    '<div class="info-banner">'
    '👋 Welcome! I\'m your AI screening assistant from <b>TalentScout</b>. '
    'I\'ll collect your details and ask a few technical questions. '
    'Type <b>exit</b> or <b>bye</b> at any time to end the session.'
    '</div>',
    unsafe_allow_html=True,
)

# ─────────────────────────── INITIALIZE CHAT ──────────────────────────
if not st.session_state.initialized:
    with st.spinner("Starting your screening session…"):
        opening = call_ai(
            "Begin the candidate screening. "
            "Greet the candidate warmly and ask for their full name."
        )
    st.session_state.display.append(("assistant", opening))
    st.session_state.initialized = True

# ─────────────────────────── DISPLAY MESSAGES ─────────────────────────
for role, msg in st.session_state.display:
    avatar = "🤖" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg)

# ─────────────────────────── USER INPUT ───────────────────────────────
if not st.session_state.ended:
    user_input = st.chat_input("Type your response here…")

    if user_input:
        # Show user message immediately
        st.session_state.display.append(("user", user_input))

        # Exit keyword check
        if is_exit(user_input):
            farewell = (
                "Thank you so much for your time today! 🎉 "
                "Your responses have been noted and a TalentScout recruiter "
                "will be in touch within 3–5 business days. "
                "Best of luck with your application — have a wonderful day! 👋"
            )
            st.session_state.display.append(("assistant", farewell))
            st.session_state.stage_index = 5
            st.session_state.ended = True

        else:
            with st.spinner("Thinking…"):
                reply = call_ai(user_input)
            st.session_state.display.append(("assistant", reply))

            # Auto-detect natural conversation end
            end_signals = [
                "recruiter will be in touch",
                "best of luck",
                "screening is complete",
                "screening is now complete",
                "we'll be in touch",
                "goodbye",
                "take care",
                "have a great day",
                "have a wonderful",
            ]
            if any(sig in reply.lower() for sig in end_signals):
                st.session_state.ended = True

        st.rerun()

else:
    # ── Completion banner ──
    st.success(
        "✅ **Screening Complete!** "
        "A TalentScout recruiter will reach out within 3–5 business days."
    )
    if st.button("🔄 Start a New Screening", use_container_width=True):
        for k in list(defaults.keys()):
            st.session_state[k] = defaults[k]
        st.rerun()
