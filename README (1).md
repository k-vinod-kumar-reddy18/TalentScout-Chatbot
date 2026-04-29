# 🎯 TalentScout — AI Hiring Assistant Chatbot

An AI-powered hiring assistant chatbot that conducts structured candidate screenings — collecting personal details and generating technical interview questions based on each candidate's declared tech stack.

Built with **Streamlit** and powered by **Groq API (llama-3.1-8b-instant)**.

---

## 🚀 Live Demo

👉 [Open App](https://talentscout-chatbot-lgunupnt3yqqcngnvw5uzm.streamlit.app/)

---

## 🎥 Demo Video

👉 [Watch Demo](https://drive.google.com/file/d/1B_WTJRbhb1HIiyAn0d9DCElMdID5_EQU/view?usp=sharing)

---

## 🧠 How It Works

The chatbot follows a fixed **6-stage screening flow**:

| Stage | What It Does |
|-------|-------------|
| 1. Greeting | Welcomes the candidate and asks for their full name |
| 2. Contact Info | Collects email, phone, and location (one at a time) |
| 3. Professional Background | Asks about experience and desired role |
| 4. Tech Stack | Candidate lists all technologies they know |
| 5. Technical Assessment | Generates 3–5 questions based on the declared stack |
| 6. Closing | Thanks candidate and informs them a recruiter will follow up |

---

## ✨ Features

- **One question at a time** — never overwhelming the candidate
- **Dynamic question generation** — questions are based only on what the candidate declares, not a fixed bank
- **Context-aware** — full conversation history sent every API call, so nothing gets repeated
- **Exit keyword detection** — type `exit`, `bye`, or `quit` to end anytime
- **Progress sidebar** — visual progress bar + stage list so candidates know where they are
- **Candidate profile extraction** — structured JSON profile auto-extracted at closing and shown in sidebar
- **Off-topic fallback** — redirects candidate back to screening if they go off-topic
- **Restart button** — start a fresh screening session anytime

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend / UI | Streamlit |
| LLM API | Groq API |
| Model | llama-3.1-8b-instant |
| Language | Python 3.10+ |
| Deployment | Streamlit Community Cloud |

---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/k-vinod-kumar-reddy18/TalentScout-Chatbot.git
cd TalentScout-Chatbot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set your Groq API key
Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_groq_api_key_here
```

Or export it directly:
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

### 4. Run the app
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
TalentScout-Chatbot/
├── app.py              # Main Streamlit app (UI + API + prompt + logic)
├── requirements.txt    # Python dependencies
├── .env                # API key (not committed to GitHub)
├── .gitignore
└── README.md
```

---

## 🔒 Data Privacy

- No candidate data is saved to disk or any external database
- All session data lives in Streamlit's in-memory session state
- Data is cleared when the browser tab closes or a new session starts

---

## 📄 License

MIT — free to use and modify.
