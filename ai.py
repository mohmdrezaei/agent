# ai.py
from flask import Flask, request, jsonify, session
from codewords_client import AsyncCodewordsClient
import asyncio
import os
import uuid
from datetime import datetime

# تنظیمات
app = Flask(__name__)
app.secret_key = "super-secret-key-change-in-production-123456789"  # تغییرش بده اگه می‌خوای امن باشه

# کلید API (بهتره از محیط استفاده کنی، ولی الان مستقیم گذاشتم)
os.environ["CODEWORDS_API_KEY"] = "cwk-6fc38fb4dae24cb280b863ec32328a9eaa9b1ffcbe3b7840cb9015750ae75cb3"

# HTML کامل چت (همه چیز داخل همین فایل!)
HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>چت‌بات قوانین آموزشی دانشگاه</title>
    <style>
        * { margin:pery: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Tahoma, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; display: flex; justify-content: center; align-items: center; padding: 10px; }
        .container { width: 100%; max-width: 800px; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 15px 40px rgba(0,0,0,0.3); display: flex; flex-direction: column; height: 95vh; }
        .header { background: #075e54; color: white; padding: 20px; text-align: center; }
        .header h1 { font-size: 22px; }
        .header p { font-size: 14px; opacity: 0.9; }
        .messages { flex: 1; padding: 20px; overflow-y: auto; background: #ece5dd; }
        .msg { margin: 15px 0; display: flex; animation: fadeIn 0.4s; }
        .msg.user { justify-content: flex-start; }
        .msg.bot { justify-content: flex-end; }
        .bubble { max-width: 80%; padding: 14px 18px; border-radius: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); line-height: 1.6; }
        .user .bubble { background: #dcf8c6; border-bottom-left-radius: 4px; }
        .bot .bubble { background: white; border-bottom-right-radius: 4px; }
        .time { font-size: 11px; color: #999; margin-top: 5px; text-align: left; }
        .input-area { padding: 15px; background: #f0f0f0; display: flex; gap: 10px; }
        input { flex: 1; padding: 16px; border: none; border-radius: 30px; font-size: 16px; }
        input:focus { outline: 3px solid #075e54; }
        button { padding: 16px 30px; background: #075e54; color: white; border: none; border-radius: 30px; cursor: pointer; font-weight: bold; }
        button:hover { background: #064c44; }
        button:disabled { background: #999; }
        .new-session { background: #dc3545; }
        .new-session:hover { background: #c82333; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>دستیار قوانین آموزشی دانشگاه</h1>
            <p>مکالمه شما محرمانه است و ذخیره نمی‌شود</p>
        </div>
        <div class="messages" id="messages">
            <div class="msg bot"><div class="bubble">سلام! خوش آمدید<br>سوالتون در مورد قوانین آموزشی چیه؟</div></div>
        </div>
        <div class="input-area">
            <input type="text" id="question" placeholder="سوال خود را اینجا بنویسید..." autocomplete="off">
            <button onclick="send()">ارسال</button>
            <button class="new-session" onclick="newSession()">جدید</button>
        </div>
    </div>

    <script>
        const messages = document.getElementById('messages');
        const input = document.getElementById('question');

        function addMessage(sender, text, time = new Date().toLocaleTimeString('fa-IR', {hour: '2-digit', minute: '2-digit'})) {
            const div = document.createElement('div');
            div.className = `msg ${sender}`;
            div.innerHTML = `<div class="bubble">${text.replace(/\\n/g, '<br>')}</div><div class="time">${time}</div>`;
            messages.appendChild(div);
            messages.scrollTop = messages.scrollHeight;
        }

        async function send() {
            const q = input.value.trim();
            if (!q) return;
            addMessage('user', q);
            input.value = '';
            const btn = document.querySelector('button');
            btn.disabled = true;
            btn.textContent = 'در حال ارسال...';

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({question: q})
                });
                const data = await res.json();
                if (data.error) throw new Error(data.error);
                addMessage('bot', data.answer, data.timestamp);
            } catch (e) {
                addMessage('bot', 'خطا: ' + e.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'ارسال';
            }
        }

        async function newSession() {
            if (!confirm('مطمئنی می‌خوای مکالمه جدید شروع کنی؟')) return;
            await fetch('/api/new-session', {method: 'POST'});
            messages.innerHTML = '';
            addMessage('bot', 'مکالمه جدید شروع شد! سوال جدید بپرسید');
        }

        input.addEventListener('keypress', e => { if (e.key === 'Enter') send(); });
    </script>
</body>
</html>
"""

async def call_chatbot(question: str, session_id: str):
    async with AsyncCodewordsClient() as client:
        response = await client.run(
            service_id="university_rules_chatbot_67dc1e98",
            inputs={"question": question, "session_id": session_id}
        )
        response.raise_for_status()
        return response.json()

@app.route('/')
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return HTML

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "سوال خالی است"}), 400

        session_id = session.get('session_id', 'anonymous')
        result = asyncio.run(call_chatbot(question, session_id))

        return jsonify({
            "answer": result.get("answer", "پاسخی دریافت نشد"),
            "timestamp": datetime.now().strftime("%H:%M")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/new-session', methods=['POST'])
def new_session():
    session['session_id'] = str(uuid.uuid4())
    return jsonify({"message": "جوری مکالمه جدید ایجاد شد"})

# === مهم: برای Vercel ===
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)  # این خط باعث میشه روی Vercel کار کنه!

# برای اجرای لوکال (اختیاری)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai:app", host="0.0.0.0", port=5001, reload=True)