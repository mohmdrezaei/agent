from flask import Flask, request, jsonify, session
from codewords_client import AsyncCodewordsClient
import asyncio
import os
import uuid
from datetime import datetime

# تنظیمات
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secret-key-change-in-production-123456789")

# کلید API از محیط
CODEWORDS_API_KEY = os.environ.get("CODEWORDS_API_KEY", "cwk-6fc38fb4dae24cb280b863ec32328a9eaa9b1ffcbe3b7840cb9015750ae75cb3")
os.environ["CODEWORDS_API_KEY"] = CODEWORDS_API_KEY

# HTML کامل چت (همه چیز داخل همین فایل!)
HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>چت‌بات قوانین آموزشی دانشگاه</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
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
        .loading { opacity: 0.7; }
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
            <div class="msg bot">
                <div class="bubble">
                    سلام! به دستیار قوانین آموزشی دانشگاه خوش آمدید 🌟<br><br>
                    من می‌تونم در مورد موارد زیر کمک کنم:<br>
                    • قوانین ثبت‌نام و حذف و اضافه<br>
                    • مقررات تحصیلی و انضباطی<br>
                    • شرایط فارغ‌التحصیلی<br>
                    • و سایر مقررات آموزشی<br><br>
                    سوال خود را بپرسید...
                </div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="question" placeholder="سوال خود را اینجا بنویسید..." autocomplete="off">
            <button onclick="sendMessage()">ارسال</button>
            <button class="new-session" onclick="newSession()">جلسه جدید</button>
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

        function setLoading(state) {
            const btn = document.querySelector('button:not(.new-session)');
            if (state) {
                btn.disabled = true;
                btn.textContent = 'در حال ارسال...';
                input.disabled = true;
            } else {
                btn.disabled = false;
                btn.textContent = 'ارسال';
                input.disabled = false;
            }
        }

        async function sendMessage() {
            const question = input.value.trim();
            if (!question) {
                alert('لطفاً سوال خود را وارد کنید');
                return;
            }

            // نمایش سوال کاربر
            addMessage('user', question);
            input.value = '';
            setLoading(true);

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: question
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || 'خطای سرور');
                }

                addMessage('bot', data.answer, data.timestamp);

            } catch (error) {
                console.error('Error:', error);
                addMessage('bot', '⚠️ خطا در ارتباط با سرور: ' + error.message);
            } finally {
                setLoading(false);
                input.focus();
            }
        }

        async function newSession() {
            if (!confirm('آیا مطمئن هستید که می‌خواهید جلسه جدید شروع کنید؟ تاریخچه مکالمه پاک خواهد شد.')) {
                return;
            }

            try {
                const response = await fetch('/api/new-session', {
                    method: 'POST'
                });

                if (response.ok) {
                    messages.innerHTML = '';
                    addMessage('bot', '🔄 جلسه جدید شروع شد! لطفاً سوال خود را بپرسید.');
                } else {
                    throw new Error('خطا در ایجاد جلسه جدید');
                }
            } catch (error) {
                alert('خطا در ایجاد جلسه جدید: ' + error.message);
            }
        }

        // امکان ارسال با کلید Enter
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // فوکوس خودکار روی input
        input.focus();
    </script>
</body>
</html>
"""

async def call_chatbot(question: str, session_id: str):
    """
    فراخوانی سرویس چت‌بات Codewords
    """
    try:
        print(f"📞 Calling Codewords API - Question: '{question}', Session: {session_id}")
        
        async with AsyncCodewordsClient() as client:
            response = await client.run(
                service_id="university_rules_chatbot_67dc1e98",
                inputs={
                    "question": question,
                    "session_id": session_id
                }
            )
            
            # بررسی وضعیت پاسخ
            if response.status_code != 200:
                error_msg = f"Codewords API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            
            result = response.json()
            print(f"✅ Codewords response: {result}")
            return result
            
    except Exception as e:
        print(f"❌ Error in call_chatbot: {str(e)}")
        raise

@app.route('/')
def index():
    """
    صفحه اصلی چت
    """
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        print(f"🆕 New session created: {session['session_id']}")
    
    return HTML

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    API برای ارسال سوال به چت‌بات
    """
    try:
        # بررسی وجود داده JSON
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "داده‌ای دریافت نشد"}), 400
        
        # استخراج سوال
        question = data.get('question', '').strip()
        if not question:
            return jsonify({"error": "سوال نمی‌تواند خالی باشد"}), 400
        
        # دریافت session_id
        session_id = session.get('session_id', 'anonymous')
        print(f"💬 Chat request - Question: '{question}', Session: {session_id}")
        
        # فراخوانی چت‌بات
        result = asyncio.run(call_chatbot(question, session_id))
        
        # پردازش پاسخ
        if isinstance(result, dict):
            answer = result.get("answer", "پاسخی دریافت نشد")
            # اگر answer وجود نداشت، کل result را بررسی کن
            if answer == "پاسخی دریافت نشد" and len(result) > 0:
                answer = str(result)
        else:
            answer = str(result) if result else "پاسخی دریافت نشد"
        
        response_data = {
            "answer": answer,
            "timestamp": datetime.now().strftime("%H:%M"),
            "session_id": session_id
        }
        
        print(f"✅ Chat response sent: {answer[:100]}...")
        return jsonify(response_data)
        
    except Exception as e:
        error_msg = f"خطا در پردازش سوال: {str(e)}"
        print(f"❌ Chat error: {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/api/new-session', methods=['POST'])
def new_session():
    """
    API برای شروع جلسه جدید
    """
    try:
        old_session = session.get('session_id', 'none')
        session['session_id'] = str(uuid.uuid4())
        new_session_id = session['session_id']
        
        print(f"🔄 Session renewed: {old_session} -> {new_session_id}")
        
        return jsonify({
            "message": "جلسه جدید با موفقیت ایجاد شد",
            "session_id": new_session_id
        })
        
    except Exception as e:
        error_msg = f"خطا در ایجاد جلسه جدید: {str(e)}"
        print(f"❌ New session error: {error_msg}")
        return jsonify({"error": error_msg}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    بررسی سلامت سرویس
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "session_count": 1
    })

# === پیکربندی برای Vercel ===
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)

# برای اجرای لوکال
if __name__ == "__main__":
    print("🚀 Starting University Rules Chatbot...")
    print(f"🔑 API Key: {CODEWORDS_API_KEY[:10]}...")
    
    # اجرای سرور
    import uvicorn
    uvicorn.run(
        "ai:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001)),
        reload=True
    )