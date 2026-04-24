import os
from flask import Flask, request, jsonify, send_from_directory
from groq import Groq

app = Flask(__name__, static_folder="static")

API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=API_KEY)

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


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id", "default")
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if session_id not in chat_sessions:
        chat_sessions[session_id] = []

    chat_sessions[session_id].append({
        "role": "user",
        "content": user_message
    })

    if len(chat_sessions[session_id]) > 20:
        chat_sessions[session_id] = chat_sessions[session_id][-20:]

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_sessions[session_id]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
    )

    reply = response.choices[0].message.content

    chat_sessions[session_id].append({
        "role": "assistant",
        "content": reply
    })

    return jsonify({"reply": reply})


@app.route("/reset", methods=["POST"])
def reset():
    data = request.json
    session_id = data.get("session_id", "default")
    chat_sessions.pop(session_id, None)
    return jsonify({"status": "reset"})


# if __name__ == "__main__":
#     os.makedirs("static", exist_ok=True)
#     app.run(debug=True, port=5000)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)