# TalentScout — AI Hiring Assistant

A conversational hiring assistant chatbot built for **TalentScout**, a fictional tech recruitment agency. It conducts structured initial candidate screenings by gathering essential information and generating tailored technical interview questions based on the candidate's declared tech stack.

---

## Features

- **Structured screening flow** — progresses through 6 stages: greeting → contact info → professional background → tech stack → technical assessment → closing
- **Dynamic technical question generation** — generates 3–5 intermediate-level questions tailored to the exact technologies the candidate declares
- **Context-aware conversation** — maintains full conversation history in every API call for coherent multi-turn dialogue
- **Exit keyword detection** — gracefully ends the session when the candidate types keywords like `exit`, `bye`, `quit`, etc.
- **Fallback handling** — stays on-topic and redirects off-topic responses
- **Progress indicator** — visual progress bar and stage label shows where the candidate is in the screening
- **Restart capability** — candidates can start a fresh session after completion

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend / UI | Streamlit |
| LLM | Claude (`claude-sonnet-4-20250514`) via Anthropic API |
| API Client | `anthropic` Python SDK |
| Language | Python 3.10+ |

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/talentscout-hiring-assistant.git
cd talentscout-hiring-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key

Create a `.env` file in the project root:

```
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

Or export it directly:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."    # macOS / Linux
set ANTHROPIC_API_KEY=sk-ant-...          # Windows
```

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage

1. Open the app in your browser
2. The assistant greets you automatically and asks for your full name
3. Answer each question naturally — one at a time
4. When asked for your tech stack, list everything you know (e.g. "Python, Django, PostgreSQL, Docker, React")
5. The assistant will generate and ask 3–5 technical questions tailored to your stack
6. After the technical assessment, the conversation concludes with next steps
7. Type `exit`, `bye`, or `quit` at any point to end the session early

---

## Prompt Design

### System Prompt Architecture

The system prompt is structured in two parts:

**1. Conversation flow instructions** — The prompt explicitly defines 6 sequential stages and instructs the model to follow them in order. Each stage specifies what information to collect and how to ask for it (one question at a time, conversationally).

**2. Behavioral rules** — A separate ruleset enforces:
- Single-question-per-turn discipline (prevents overwhelming the candidate)
- Tech-stack-specific question generation (the model is instructed to match questions exactly to declared technologies)
- Context retention (never re-ask collected information)
- Off-topic redirection (keeps the conversation focused)
- Exit keyword handling (graceful session termination)

### Why this approach works

- **Stage-based prompting** prevents the model from jumping ahead or skipping required information fields
- **Explicit quality constraints** ("intermediate-level, not trivial") ensure technical questions are substantive
- **Full conversation history** is sent with every API call, so the model always has context for what has already been asked and answered
- The model naturally infers the current stage from the history without needing explicit state tracking in the prompt

---

## Project Structure

```
talentscout/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
├── .env                 # API key (not committed to git)
├── .gitignore
└── README.md
```

---

## Data Privacy

- No candidate data is persisted to disk or any external database
- All conversation state lives in Streamlit's session state (in-memory, per session)
- Session data is cleared when the browser tab closes or when the user starts a new screening
- The Anthropic API processes messages in transit — review [Anthropic's privacy policy](https://www.anthropic.com/privacy) for data handling details
- In a production deployment, you would encrypt any stored PII and implement GDPR-compliant data handling (right to access, right to erasure, data minimization)

---

## Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| Keeping the model on-topic | Explicit "do not deviate" instruction + off-topic redirection rule in system prompt |
| Preventing repeated questions | Full conversation history sent every turn; prompt instructs model to never re-ask collected info |
| Generating relevant technical questions | Prompt instructs model to wait until tech stack is declared, then generate questions precisely matched to declared technologies |
| Detecting conversation end | Dual detection: exit keywords checked client-side; closing language patterns checked in the assistant's reply |
| Single-question-per-turn discipline | Explicit rule in prompt: "Ask only ONE thing at a time. Never combine multiple questions." |

---

## Optional Enhancements (Bonus Ideas)

- **Sentiment analysis**: Use `transformers` (e.g. `cardiffnlp/twitter-roberta-base-sentiment`) to display a live sentiment gauge during the conversation
- **Multilingual support**: Detect language from first message and instruct Claude to respond in that language
- **Candidate report export**: After screening, generate a PDF summary of collected info + question responses
- **Cloud deployment**: Deploy to Streamlit Community Cloud (free) or package as a Docker container for AWS ECS

---

## License

MIT — free to use and modify.
