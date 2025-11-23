# api/index.py
from flask import Flask, request, jsonify, session
from codewords_client import AsyncCodewordsClient
import asyncio
import os
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "my-super-secret-key-2025")

# کلید از محیط گرفته می‌شه (در Vercel تنظیم کن)
os.environ["CODEWORDS_API_KEY"] = os.getenv(
    "CODEWORDS_API_KEY",
    "cwk-6fc38fb4dae24cb280b863ec32328a9eaa9b1ffcbe3b7840cb9015750ae75cb3"
)

HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>دستیار قوانین آموزشی دانشگاه</title>
    <style>
        :root { --p: #075e54; --l: #dcf8c6; }
        * { margin:0; padding:0; box-sizing:border-box; font-family:Tahoma,Arial; }
        body { background:linear-gradient(135deg,#667eea,#764ba2); min-height:100vh; display:flex; justify-content:center; align-items:center; padding:10px; }
        .box { width:100%; max-width:850px; background:white; border-radius:20px; overflow:hidden; box-shadow:0 20px 50px rgba(0,0,0,0.3); display:flex; flex-direction:column; height:95vh; }
        .h { background:var(--p); color:white; padding:20px; text-align:center; }
        .m { flex:1; padding:20px; overflow-y:auto; background:#ece5dd; }
        .msg { margin:12px 0; display:flex; animation:f 0.4s; }
        .u { justify-content:flex-start; }
        .b { justify-content:flex-end; }
        .bub { max-width:78%; padding:14px 18px; border-radius:18px; line-height:1.6; }
        .u .bub { background:var(--l); border-bottom-left-radius:4px; }
        .b .bub { background:white; border-bottom-right-radius:4px; }
        .t { font-size:10px; color:#888; margin-top:5px; }
        .in { padding:15px; background:#f8f9fa; display:flex; gap:10px; }
        input { flex:1; padding:16px; border:none; border-radius:30px; background:#fff; box-shadow:inset 0 1px 5px rgba(0,0,0,0.1); }
        input:focus { outline:3px solid var(--p); }
        button { padding:16px 28px; background:var(--p); color:white; border:none; border-radius:30px; cursor:pointer; font-weight:bold; }
        button:hover { background:#064c44; }
        .new { background:#dc3545; }
        .new:hover { background:#c82333; }
        @keyframes f { from{opacity:0; transform:translateY(10px);} to{opacity:1;} }
    </style>
</head>
<body>
<div class="box">
    <div class="h">
        <h1>دستیار قوانین آموزشی دانشگاه</h1>
        <p>هر سوالی دارید بپرسید</p>
    </div>
    <div class="m" id="m">
        <div class="msg b"><div class="bub">سلام! چطور می‌تونم کمکتون کنم؟</div></div>
    </div>
    <div class="in">
        <input type="text" id="q" placeholder="سوال خود را بنویسید..." autocomplete="off">
        <button onclick="send()">ارسال</button>
        <button class="new" onclick="newC()">جدید</button>
    </div>
</div>

<script>
    const m = document.getElementById('m');
    function add(t, s='b', time=new Date().toLocaleTimeString('fa-IR',{hour:'2-digit',minute:'2-digit'})) {
        const d = document.createElement('div');
        d.className = `msg ${s==='u'?'u':'b'}`;
        d.innerHTML = `<div class="bub">${t.replace(/\\n/g,'<br>')}</div><div class="t">${time}</div>`;
        m.appendChild(d); m.scrollTop = m.scrollHeight;
    }
    async function send() {
        const i = document.getElementById('q');
        const q = i.value.trim(); if (!q) return;
        add(q, 'u'); i.value = '';
        const b = document.querySelector('button'); b.disabled=true; b.textContent='در حال فکر...';
        try {
            const r = await fetch('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question:q})});
            const d = await r.json();
            if (d.error) throw new Error(d.error);
            add(d.answer || "بدون پاسخ");
        } catch(e) { add("خطا: "+e.message, 'b'); }
        finally { b.disabled=false; b.textContent='ارسال'; }
    }
    async function newC() {
        if(confirm("مکالمه جدید؟")) {
            await fetch('/api/new-session', {method:'POST'});
            m.innerHTML=''; add("مکالمه جدید شروع شد");
        }
    }
    document.getElementById('q').addEventListener('keypress', e=>e.key==='Enter'&&send());
</script>
</body>
</html>
"""

async def call_api(question: str, sid: str):
    async with AsyncCodewordsClient() as client:
        payload = {"question": question.strip(), "session_id": str(sid)}
        print("ارسال به CodeWords:", payload)
        resp = await client.run(
            service_id="university_rules_chatbot_67dc1e98",
            inputs=payload
        )
        if not resp.ok:
            err = await resp.text()
            print(f"خطای CodeWords: {resp.status} {err}")
            raise Exception(f"CodeWords Error: {err}")
        return resp.json()

@app.route('/')
def home():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return HTML

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True) or {}
        q = data.get("question", "").strip()
        if len(q) < 2:
            return jsonify({"error": "سوال خیلی کوتاه است"}), 400
        sid = session.get('sid', str(uuid.uuid4()))
        result = asyncio.run(call_api(q, sid))
        return jsonify({"answer": result.get("answer", "پاسخی دریافت نشد")})
    except Exception as e:
        msg = str(e)
        print("خطای کامل:", msg)
        return jsonify({"error": msg}), 500

@app.route('/api/new-session', methods=['POST'])
def new_session():
    session['sid'] = str(uuid.uuid4())
    return jsonify({"ok": True})

# برای Vercel (حتماً این دو خط آخر باشه!)
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)

# برای لوکال
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("index:app", host="0.0.0.0", port=5001, reload=True)