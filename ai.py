# ai.py - نسخه ۱۰۰٪ کارکرده روی Vercel + رفع 422
from flask import Flask, request, jsonify, session
from codewords_client import AsyncCodewordsClient
import asyncio
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-fallback-key-2025")

# کلید رو از محیط می‌گیره (امن‌تر) - در Vercel تنظیم کن
CODEWORDS_API_KEY = os.getenv("CODEWORDS_API_KEY", "cwk-6fc38fb4dae24cb280b863ec32328a9eaa9b1ffcbe3b7840cb9015750ae75cb3")
os.environ["CODEWORDS_API_KEY"] = CODEWORDS_API_KEY

# HTML کامل و زیبا
HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>دستیار قوانین آموزشی دانشگاه</title>
    <style>
        :root { --primary: #075e54; --light: #dcf8c6; --bg: #f0f2f5; }
        * { margin:0; padding:0; box-sizing:border-box; font-family:Tahoma,Arial,sans-serif; }
        body { background: linear-gradient(135deg, #667eea, #764ba2); min-height:100vh; display:flex; justify-content:center; align-items:center; padding:10px; }
        .chat-container { width:100%; max-width:850px; background:white; border-radius:20px; overflow:hidden; box-shadow:0 20px 50px rgba(0,0,0,0.3); display:flex; flex-direction:column; height:95vh; }
        .header { background:var(--primary); color:white; padding:20px; text-align:center; }
        .header h1 { font-size:24px; }
        .header p { font-size:14px; opacity:0.9; margin-top:5px; }
        .messages { flex:1; padding:20px; overflow-y:auto; background:#ece5dd; }
        .msg { margin:12px 0; display:flex; animation:fade 0.4s; }
        .msg.user { justify-content:flex-start; }
        .msg.bot { justify-content:flex-end; }
        .bubble { max-width:78%; padding:14px 18px; border-radius:18px; line-height:1.6; word-wrap:break-word; }
        .user .bubble { background:var(--light); border-bottom-left-radius:4px; }
        .bot .bubble { background:white; border-bottom-right-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.1); }
        .time { font-size:10px; color:#888; margin-top:4px; }
        .input-area { padding:15px; background:#f8f9fa; display:flex; gap:10px; border-top:1px solid #ddd; }
        input { flex:1; padding:16px 20px; border:none; border-radius:30px; font-size:16px; background:#fff; box-shadow:0 1px 5px rgba(0,0,0,0.1); }
        input:focus { outline:3px solid var(--primary); }
        button { padding:16px 28px; background:var(--primary); color:white; border:none; border-radius:30px; cursor:pointer; font-weight:bold; }
        button:hover { background:#064c44; }
        .new-btn { background:#dc3545; }
        .new-btn:hover { background:#c82333; }
        @keyframes fade { from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:none;} }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">
            <h1>دستیار قوانین آموزشی</h1>
            <p>هر سوالی در مورد آیین‌نامه، مرخصی، حذف ترم و ... دارید بپرسید</p>
        </div>
        <div class="messages" id="messages">
            <div class="msg bot"><div class="bubble">سلام! چطور می‌تونم کمکتون کنم؟</div></div>
        </div>
        <div class="input-area">
            <input type="text" id="q" placeholder="سوال خود را اینجا بنویسید..." autocomplete="off">
            <button onclick="send()">ارسال</button>
            <button class="new-btn" onclick="newChat()">جدید</button>
        </div>
    </div>

    <script>
        const msgs = document.getElementById('messages');
        function add(text, sender = 'bot', time = new Date().toLocaleTimeString('fa-IR',{hour:'2-digit',minute:'2-digit'})) {
            const div = document.createElement('div');
            div.className = `msg ${sender}`;
            div.innerHTML = `<div class="bubble">${text.replace(/\\n/g,'<br>')}</div><div class="time">${time}</div>`;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
        }
        async function send() {
            const input = document.getElementById('q');
            const q = input.value.trim();
            if (!q) return;
            add(q, 'user');
            input.value = '';
            const btn = document.querySelector('button');
            btn.disabled = true; btn.textContent = 'در حال فکر...';

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: q})
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);
                add(data.answer || "پاسخی دریافت نشد");
            } catch (e) {
                add("خطا: " + e.message, 'bot');
            } finally {
                btn.disabled = false; btn.textContent = 'ارسال';
            }
        }
        async function newChat() {
            if (confirm("مطمئنی مکالمه جدید شروع بشه؟")) {
                await fetch('/api/new-session', {method:'POST'});
                msgs.innerHTML = ''; add("مکالمه جدید شروع شد");
            }
        }
        document.getElementById('q').addEventListener('keypress', e => e.key==='Enter' && send());
    </script>
</body>
</html>
"""

# فراخوانی ایمن API با نمایش خطای دقیق
async def call_codewords(question: str, session_id: str):
    async with AsyncCodewordsClient() as client:
        payload = {
            "question": question.strip(),
            "session_id": str(session_id) if session_id else str(uuid.uuid4())
        }
        print(f"ارسال به CodeWords: {payload}")
        response = await client.run(
            service_id="university_rules_chatbot_67dc1e98",
            inputs=payload
        )
        if not response.ok:
            error_text = await response.text()
            print(f"خطای API CodeWords: {response.status} {error_text}")
            raise Exception(f"API Error {response.status}: {error_text}")
        return response.json()

@app.route('/')
def index():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return HTML

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True)
        question = data.get("question", "").strip()
        if not question or len(question) < 2:
            return jsonify({"error": "سوال خیلی کوتاه است"}), 400

        sid = session.get('sid', str(uuid.uuid4()))
        result = asyncio.run(call_codewords(question, sid))

        return jsonify({
            "answer": result.get("answer", "بدون پاسخ"),
            "timestamp": datetime.now().strftime("%H:%M")
        })
    except Exception as e:
        error_detail = str(e)
        print(f"خطای کامل: {error_detail}")
        return jsonify({"error": error_detail}), 500

@app.route('/api/new-session', methods=['POST'])
def new_session():
    session['sid'] = str(uuid.uuid4())
    return jsonify({"message": "جلسه جدید ایجاد شد"})

# برای Vercel (حتماً این دو خط آخر باشه!)
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)

# برای اجرای لوکال
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai:app", host="0.0.0.0", port=5001, reload=True)