# 💻 LaptopBot — AI Laptop Troubleshooter

A specialized AI chatbot built with Python (Flask) + Claude API that helps users diagnose and fix laptop issues.

---

## 🚀 Quick Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Set your Anthropic API key
```bash
# Linux / macOS
export ANTHROPIC_API_KEY="your_key_here"

# Windows (CMD)
set ANTHROPIC_API_KEY=your_key_here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your_key_here"
```

### 3. Run the app
```bash
python app.py
```

### 4. Open your browser
```
http://localhost:5000
```

---

## 📁 Project Structure

```
laptop_chatbot/
├── app.py              # Flask backend + Claude API integration
├── requirements.txt    # Python dependencies
├── README.md
└── static/
    └── index.html      # Frontend UI
```

---

## ✨ Current Features

- 🤖 Powered by Claude claude-opus-4-5 with a laptop-specialist system prompt
- 💬 Full multi-turn conversation memory per session
- 🚀 8 quick-access chips for common issues
- 💅 Polished dark-mode UI with typing indicators
- 🔄 Session reset / clear chat
- 📱 Responsive layout

---

## 🔧 Improvement Ideas (Implement These!)

### 🟢 Easy Wins
1. **Streaming responses** — Use `client.messages.stream()` for real-time token streaming so the reply appears word-by-word (much better UX).
2. **Copy button** — Add a clipboard icon on bot messages to copy the fix steps.
3. **Markdown renderer** — Use `marked.js` in the frontend for proper rendering of bold, lists, and code blocks.
4. **Persistent chat history** — Save conversations to a SQLite DB with `sqlite3` so sessions survive server restarts.
5. **OS detection chip** — Ask users their OS (Windows/macOS/Linux) at the start and include it in every message.

### 🟡 Medium Difficulty
6. **Diagnostic tool runner** — Add a button that generates a Python/PowerShell script users can run locally to collect system info (CPU%, RAM, disk, OS version) and paste back.
7. **Issue categorizer** — Classify each user message into a category (Performance / Hardware / Software / Network) and show a colored tag on the message.
8. **Feedback system** — Thumbs up/down on bot messages. Store ratings in SQLite and log which answers were unhelpful.
9. **Context-aware follow-ups** — After a solution, auto-suggest 2-3 follow-up chips ("Issue still persists", "How to prevent this", "Show advanced steps").
10. **Multi-language support** — Detect user language via `langdetect` and respond in the same language.

### 🔴 Advanced
11. **RAG with laptop docs** — Index a PDF library of laptop manuals / manufacturer guides with `chromadb` + `sentence-transformers`. Retrieve relevant docs before answering.
12. **Screenshot analysis** — Let users upload a screenshot of an error message or Task Manager. Use Claude's vision capabilities to analyze it.
13. **Severity scoring** — Rate each reported issue (1–5 severity) and show a colored badge. Urgent issues get a "Seek professional repair" warning.
14. **Admin dashboard** — A `/admin` page showing total sessions, most common issue categories, average session length, and unsatisfied sessions.
15. **Voice input** — Use the Web Speech API (`SpeechRecognition`) so users can speak their problem instead of typing.
16. **Proactive diagnostics** — After 3 turns of unresolved issues, suggest a structured diagnostic checklist tailored to the problem.

---

## 📌 Notes
- The chatbot is scoped to laptop/software topics. It politely redirects unrelated questions.
- Session history is stored in memory. Restart the server to clear all sessions.
- Max 20 messages kept per session to avoid token overflow.
