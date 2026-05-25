import os
import sqlite3
import uuid
from datetime import datetime, timezone

from flask import Flask, request, jsonify, send_from_directory
from groq import Groq

app = Flask(__name__, static_folder="static")

API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=API_KEY)

DB_PATH = os.path.join(os.path.dirname(__file__), "chat_history.db")

SYSTEM_PROMPT = """You are LaptopBot — a highly specialized AI assistant for laptop and software troubleshooting.

Your expertise covers:
- Performance issues (slow laptop, high CPU/RAM usage, overheating, freezing, hanging)
- Software problems (app crashes, installation failures, update errors, compatibility issues)
- Operating system issues (Windows, macOS, Linux boot problems, BSOD, kernel panics)
- Hardware diagnostics (battery drain, display issues, keyboard/touchpad problems, port failures)
- Network & connectivity (WiFi drops, Bluetooth pairing, VPN issues)
- Storage & files (disk full, corrupted files, recovery, SSD vs HDD)
- Security & malware (virus removal, suspicious processes, firewall settings)
- Driver issues (outdated drivers, device not recognized, audio/video problems)

Guidelines:
1. Ask clarifying questions to narrow down the problem (OS, laptop brand/model if relevant).
2. Provide step-by-step solutions — numbered, clear, actionable.
3. Start with the easiest/safest fix first, then escalate.
4. Warn before any risky steps (e.g., registry edits, data loss risk).
5. If a problem requires physical disassembly, say so clearly.
6. Be concise — use bullet points and numbered lists.
7. Always end with a follow-up like "Did that fix the issue?" or "Which step are you on?"
Only help with laptop/software topics. Politely redirect unrelated questions."""

chat_sessions = {}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        cur.execute(
            """CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )"""
        )
        conn.commit()
    finally:
        conn.close()


init_db()


@app.route("/")
def index():
    return send_from_directory("static", "index.html")



@app.route("/new_session", methods=["POST"])
def new_session():
    data = request.json or {}
    title = (data.get("title") or "New chat").strip()
    session_id = data.get("session_id") or ("session_" + uuid.uuid4().hex)

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        now = utc_now_iso()
        cur.execute(
            "INSERT OR IGNORE INTO chat_sessions(id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, title, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    # Also seed the in-memory cache so the chat endpoint stays compatible.
    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    return jsonify({"session_id": session_id, "title": title})


@app.route("/sessions", methods=["GET"])
def sessions():
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id, title, created_at, updated_at
               FROM chat_sessions
               ORDER BY updated_at DESC"""
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    items = []
    for r in rows:
        items.append({
            "id": r[0],
            "title": r[1],
            "created_at": r[2],
            "updated_at": r[3],
        })

    return jsonify({"sessions": items})


@app.route("/history/<session_id>", methods=["GET"])
def history(session_id):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT role, content
               FROM chat_messages
               WHERE session_id = ?
               ORDER BY id ASC""",
            (session_id,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    messages = [{"role": role, "content": content} for (role, content) in rows]
    return jsonify({"messages": messages})


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    session_id = data.get("session_id", "default")
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400


    # Ensure session exists in DB
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        now = utc_now_iso()
        cur.execute(
            "INSERT OR IGNORE INTO chat_sessions(id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, "New chat", now, now),
        )
        # Persist the user message
        cur.execute(
            "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES (?, 'user', ?, ?)",
            (session_id, user_message, now),
        )
        conn.commit()

        # Load last 20 turns (messages) for context (user+assistant)
        cur.execute(
            """SELECT role, content
               FROM chat_messages
               WHERE session_id = ?
               ORDER BY id DESC
               LIMIT 20""",
            (session_id,),
        )
        recent = cur.fetchall()[::-1]

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
            {"role": role, "content": content} for (role, content) in recent
        ]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
        )

        reply = response.choices[0].message.content

        # Persist assistant reply
        now2 = utc_now_iso()
        cur.execute(
            "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)",
            (session_id, reply, now2),
        )
        cur.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (now2, session_id),
        )
        conn.commit()

    finally:
        conn.close()

    # Keep in-memory cache in sync (optional; mostly for backwards compatibility)
    chat_sessions.setdefault(session_id, [])

    return jsonify({"reply": reply})



@app.route("/reset", methods=["POST"])
def reset():
    data = request.json or {}
    session_id = data.get("session_id", "default")

    # Delete messages for that session (keep session record)
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()

    chat_sessions.pop(session_id, None)
    chat_sessions[session_id] = []
    return jsonify({"status": "reset"})



# if __name__ == "__main__":
#     os.makedirs("static", exist_ok=True)
#     app.run(debug=True, port=5000)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)