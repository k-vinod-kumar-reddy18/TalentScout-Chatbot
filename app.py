"""
TalentScout Hiring Assistant
A Streamlit-based AI hiring assistant that screens tech candidates
using Claude via the Anthropic API.
"""

import streamlit as st
from anthropic import Anthropic

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TalentScout — Hiring Assistant",
    page_icon="🎯",
    layout="centered",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { max-width: 760px; margin: 0 auto; }
    .chat-header {
        background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .chat-header h2 { margin: 0; font-size: 1.4rem; }
    .chat-header p  { margin: 4px 0 0; font-size: 0.85rem; opacity: 0.82; }
    .stage-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 2px 10px;
        font-size: 0.75rem;
        margin-top: 6px;
    }
    .stChatMessage { border-radius: 10px !important; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a professional Hiring Assistant for TalentScout, a recruitment agency
specializing in technology placements. Conduct structured initial candidate screening.

CONVERSATION FLOW — follow these stages in order:
1. GREETING: Introduce yourself warmly and explain the process. Ask for full name first.
2. CONTACT INFO: Collect email address and phone number (one at a time).
3. PROFESSIONAL DETAILS: Ask for years of experience, desired position(s), and current location (one at a time).
4. TECH STACK: Ask the candidate to list their tech stack — programming languages, frameworks, databases, and tools.
5. TECHNICAL QUESTIONS: Based on their declared tech stack, generate exactly 3–5 relevant technical questions. Ask them one at a time, briefly acknowledge each answer before the next.
6. CLOSING: Thank the candidate, summarize what was collected (name, position, tech stack), and explain next steps (team review within 2–3 business days, email follow-up).

IMPORTANT RULES:
- Ask only ONE thing at a time. Never combine multiple questions.
- Be conversational and encouraging. Use the candidate's first name once you know it.
- Technical questions should be intermediate-level — not trivial, not overly complex.
- Tailor technical questions precisely to the declared tech stack.
- If candidate goes off-topic: "Great! Let's stay focused on the screening. [next question]"
- If candidate uses an exit keyword (exit, quit, bye, goodbye, end, stop) — close gracefully.
- Never make up information. Never deviate from the hiring assistant purpose.
- Keep responses concise: 2–4 sentences max (technical questions can be slightly longer).
- Never re-ask information already provided.
""".strip()

EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop", "done"}

STAGES = [
    ("Welcome", 5),
    ("Gathering contact info", 25),
    ("Collecting experience details", 45),
    ("Tech stack declaration", 65),
    ("Technical assessment", 85),
    ("Screening complete", 100),
]

# ── Session state init ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],          # {role, content} dicts for Claude API
        "display_messages": [],  # {role, content} for UI display
        "stage_index": 0,
        "ended": False,
        "client": Anthropic(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── Helper functions ───────────────────────────────────────────────────────────
def is_exit(text: str) -> bool:
    """Check if the user intends to end the conversation."""
    words = text.lower().strip().split()
    return bool(set(words) & EXIT_KEYWORDS)


def infer_stage(assistant_count: int) -> int:
    """Estimate conversation stage from number of assistant turns."""
    if assistant_count == 0: return 0
    if assistant_count <= 2: return 1
    if assistant_count <= 4: return 2
    if assistant_count <= 6: return 3
    if assistant_count <= 11: return 4
    return 5


def call_claude(user_text: str) -> str:
    """Send conversation history + new user message to Claude and return reply."""
    st.session_state.messages.append({"role": "user", "content": user_text})

    response = st.session_state.client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=st.session_state.messages,
    )
    reply = response.content[0].text.strip()
    st.session_state.messages.append({"role": "assistant", "content": reply})
    return reply


def handle_send(user_input: str):
    """Process user input: update UI history, call Claude, update stage."""
    if not user_input.strip() or st.session_state.ended:
        return

    st.session_state.display_messages.append({"role": "user", "content": user_input})

    with st.spinner("TalentScout is thinking…"):
        reply = call_claude(user_input)

    st.session_state.display_messages.append({"role": "assistant", "content": reply})

    # Update stage
    assistant_turns = sum(1 for m in st.session_state.messages if m["role"] == "assistant")
    st.session_state.stage_index = infer_stage(assistant_turns)

    # Detect natural end
    lower = reply.lower()
    if is_exit(user_input) or (
        "thank you" in lower and any(k in lower for k in ("next step", "within", "team will", "business day"))
    ):
        st.session_state.ended = True
        st.session_state.stage_index = 5


# ── Greeting on first load ─────────────────────────────────────────────────────
if not st.session_state.display_messages:
    with st.spinner("Connecting to TalentScout…"):
        opening = call_claude("Hello, I am a candidate starting my screening.")
    st.session_state.display_messages.append({"role": "assistant", "content": opening})

# ── UI: Header ─────────────────────────────────────────────────────────────────
stage_name, stage_pct = STAGES[st.session_state.stage_index]
st.markdown(f"""
<div class="chat-header">
  <h2>🎯 TalentScout Hiring Assistant</h2>
  <p>Tech candidate screening · Powered by Claude</p>
  <span class="stage-badge">{stage_name}</span>
</div>
""", unsafe_allow_html=True)

# Progress bar
st.progress(stage_pct / 100)

# ── UI: Chat history ───────────────────────────────────────────────────────────
for msg in st.session_state.display_messages:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.write(msg["content"])

# ── UI: End card ───────────────────────────────────────────────────────────────
if st.session_state.ended:
    st.success(
        "✅ **Screening complete!**  \n"
        "Our team will review your profile and reach out within 2–3 business days. Good luck!"
    )
    if st.button("🔄 Start a new screening"):
        for key in ["messages", "display_messages", "stage_index", "ended"]:
            del st.session_state[key]
        st.rerun()

# ── UI: Input ──────────────────────────────────────────────────────────────────
else:
    if user_input := st.chat_input("Type your message… (or 'exit' to end)"):
        handle_send(user_input)
        st.rerun()
