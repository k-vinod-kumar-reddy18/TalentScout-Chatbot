import streamlit as st
from anthropic import Anthropic
import os

# ── Page config ─────────────────────────────────────────────
st.set_page_config(
    page_title="TalentScout — Hiring Assistant",
    page_icon="🎯",
    layout="centered",
)

# ── LOAD API KEY ────────────────────────────────────────────
import os

api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    st.error("❌ API key not found")
    st.stop()

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
.stApp { max-width: 760px; margin: 0 auto; }
.chat-header {
    background: linear-gradient(135deg, #2d6a4f 0%, #1b4332 100%);
    color: white;
    padding: 1.2rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}
.stage-badge {
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.75rem;
}
</style>
""", unsafe_allow_html=True)

# ── SYSTEM PROMPT ───────────────────────────────────────────
SYSTEM_PROMPT = """You are a professional Hiring Assistant for TalentScout..."""

EXIT_KEYWORDS = {"exit", "quit", "bye", "goodbye", "end", "stop"}

STAGES = [
    ("Welcome", 5),
    ("Contact Info", 25),
    ("Experience", 45),
    ("Tech Stack", 65),
    ("Technical Round", 85),
    ("Completed", 100),
]

# ── INIT STATE ──────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "display_messages": [],
        "stage_index": 0,
        "ended": False,
        "client": Anthropic(api_key=api_key),  # ✅ FIXED
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── FUNCTIONS ───────────────────────────────────────────────
def is_exit(text):
    return any(word in text.lower() for word in EXIT_KEYWORDS)


def call_claude(user_text):
    try:
        st.session_state.messages.append({"role": "user", "content": user_text})

        response = st.session_state.client.messages.create(
            model="claude-3-sonnet-20240229",  # ✅ safer model
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=st.session_state.messages,
        )

        reply = response.content[0].text.strip()
        st.session_state.messages.append({"role": "assistant", "content": reply})

        return reply

    except Exception as e:
        return f"❌ Error: {e}"


def handle_send(user_input):
    if not user_input.strip() or st.session_state.ended:
        return

    st.session_state.display_messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        reply = call_claude(user_input)

    st.session_state.display_messages.append({"role": "assistant", "content": reply})

    if is_exit(user_input):
        st.session_state.ended = True
        st.session_state.stage_index = 5


# ── FIRST MESSAGE ───────────────────────────────────────────
if not st.session_state.display_messages:
    opening = call_claude("Hello, I am a candidate starting my screening.")
    st.session_state.display_messages.append({"role": "assistant", "content": opening})

# ── UI ──────────────────────────────────────────────────────
stage_name, stage_pct = STAGES[st.session_state.stage_index]

st.markdown(f"""
<div class="chat-header">
<h2>🎯 TalentScout Hiring Assistant</h2>
<p>Powered by Claude</p>
<span class="stage-badge">{stage_name}</span>
</div>
""", unsafe_allow_html=True)

st.progress(stage_pct / 100)

# Chat history
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# End state
if st.session_state.ended:
    st.success("✅ Screening complete!")
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()

# Input
else:
    if user_input := st.chat_input("Type your message..."):
        handle_send(user_input)
        st.rerun()
