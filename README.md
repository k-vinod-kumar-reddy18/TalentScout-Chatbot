# 🎯 TalentScout — AI Hiring Assistant

An intelligent conversational hiring assistant chatbot built for **TalentScout**, a fictional technology recruitment agency. The chatbot conducts structured initial candidate screenings — collecting personal and professional information, then generating tailored technical interview questions based on the candidate's declared tech stack.

---

## 🚀 Live Demo

> Run locally using the instructions below.  
> Demo video: *(attach Loom link here)*

---

## ✨ Features

| Feature | Description |
|---|---|
| **Structured 6-Stage Flow** | Greeting → Contact Info → Background → Tech Stack → Technical Assessment → Closing |
| **Dynamic Question Generation** | Generates 3–5 intermediate-level questions tailored exactly to the candidate's declared technologies |
| **Context-Aware Conversation** | Full conversation history sent every API call — never re-asks collected info |
| **Exit Keyword Detection** | Gracefully ends session on keywords like `exit`, `bye`, `quit`, `stop` |
| **Fallback Handling** | Stays on-topic and redirects any off-topic or unexpected inputs |
| **Progress Tracker** | Sidebar shows current stage, progress bar, and all 6 stages with status icons |
| **Auto Candidate Profile** | Extracts candidate JSON from closing message and populates a sidebar profile card |
| **Custom Dark UI** | Polished dark-mode Streamlit interface with custom CSS styling |
| **Restart Capability** | One-click fresh session restart from the sidebar |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend / UI | Streamlit |
| LLM | `llama-3.1-8b-instant` via Groq API |
| API Client | `groq` Python SDK |
| Language | Python 3.10+ |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/k-vinod-kumar-reddy18/TalentScout-Chatbot.git
cd TalentScout-Chatbot
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

### 4. Set your Groq API key

**Option A — .env file (recommended):**
```bash
# Create a .env file in the project root
echo GROQ_API_KEY=your_key_here > .env
```

**Option B — Export directly:**
```bash
export GROQ_API_KEY="your_key_here"     # macOS / Linux
set GROQ_API_KEY=your_key_here          # Windows
```

Get a free API key at: https://console.groq.com

### 5. Run the app
```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

## 🖥️ Usage

1. Open the app in your browser
2. The assistant greets you and asks for your full name
3. Answer each question naturally — **one at a time**
4. When asked for your tech stack, list everything (e.g. *"Python, Django, PostgreSQL, Docker, React"*)
5. The assistant generates and asks **3–5 tailored technical questions**
6. After the assessment, the session concludes with next steps
7. Type **`exit`**, **`bye`**, or **`quit`** at any point to end early

---

## 🧠 Prompt Design

### System Prompt Architecture

The system prompt is structured in three parts:

**1. Stage-based conversation flow**  
Six explicit stages are defined in order. The model is instructed to follow them strictly, collecting one piece of information per turn. This prevents the model from skipping fields or combining questions.

**2. Technical question quality constraints**  
When the tech stack is declared, the model is instructed to generate questions that are:
- Directly mapped to the specific technologies declared (not generic)
- Intermediate difficulty (not trivial, not PhD-level)
- A mix of conceptual, practical, and problem-solving types

**3. Behavioral rules**  
- Single-question-per-turn discipline
- Never re-ask already-collected information
- Off-topic redirection with a polite fallback
- Exit keyword handling → jump to graceful closing
- Hidden JSON candidate data block appended at session end

### Why This Approach Works

- **Stage-based prompting** ensures the model never skips required fields or jumps ahead
- **Full conversation history** sent every turn means the model always knows what has been asked and answered
- **Explicit quality rules** produce substantive technical questions rather than trivial ones
- **Hidden JSON block** allows clean extraction of candidate profile data without a separate API call

---

## 📁 Project Structure

```
TalentScout-Chatbot/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
├── .env                 # API key — NOT committed to git
├── .gitignore
└── README.md
```

---

## 🔒 Data Privacy

- **No data is persisted to disk or any external database**
- All conversation state lives in Streamlit's in-memory session state
- Session data is cleared when the browser tab closes or a new screening is started
- The Groq API processes messages in transit — review [Groq's privacy policy](https://groq.com/privacy-policy/) for details
- In a production deployment, PII would be encrypted at rest and GDPR-compliant handling implemented (right to access, right to erasure, data minimization)

---

## 🧩 Challenges & Solutions

| Challenge | Solution |
|---|---|
| Keeping the model strictly on-topic | Explicit fallback rule in system prompt + off-topic redirection instruction |
| Preventing repeated questions | Full conversation history sent every turn; prompt instructs model to never re-ask collected info |
| Generating relevant technical questions | Model waits until tech stack declared, then generates questions precisely matched to declared technologies |
| Single-question-per-turn discipline | Explicit rule: "Ask ONLY ONE question per turn — never bundle or combine" |
| Detecting end of conversation | Dual detection: exit keywords checked client-side; closing language patterns checked in assistant reply |
| Extracting candidate data cleanly | Hidden `<candidate_data>` JSON block in closing message, stripped before display |

---

## 🌟 Optional Enhancements (Bonus Ideas)

- **Sentiment analysis** — use `transformers` to display a live emotion gauge during conversation
- **Multilingual support** — detect language from first message and instruct the model to respond in that language
- **PDF report export** — generate a downloadable screening summary after session ends
- **Cloud deployment** — deploy to Streamlit Community Cloud (free) or containerize with Docker for AWS/GCP

---

## 📄 License

MIT — free to use and modify.
