from flask import Flask, request, jsonify, render_template_string
from codewords_client import AsyncCodewordsClient
import asyncio
import os

os.environ['CODEWORDS_API_KEY'] = 'cwk-95bb46cd9f296a1e4915e805bc2cfb5572d4cec2587235f8cb178846b64f9e13'

app = Flask(__name__)
SERVICE_ID = "university_rules_assistant_47c12da2"

HTML = """
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>دستیار قوانین دانشگاه</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:Tahoma,Arial;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:10px}
        .c{width:100%;max-width:900px;background:#fff;border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,.3);overflow:hidden}
        .h{background:linear-gradient(135deg,#1e3a8a,#3b82f6);color:#fff;padding:25px;text-align:center}
        .h h1{font-size:24px;margin-bottom:8px}
        .h p{font-size:14px;opacity:.95}
        .chat{padding:20px;background:#f3f4f6;min-height:500px;max-height:600px;overflow-y:auto}
        .m{margin:15px 0;display:flex;animation:f .4s}
        @keyframes f{from{opacity:0;transform:translateY(10px)}to{opacity:1}}
        .m.u{justify-content:flex-start}
        .m.a{justify-content:flex-end}
        .b{max-width:80%;padding:15px 20px;border-radius:15px;box-shadow:0 2px 5px rgba(0,0,0,.1);line-height:1.7}
        .m.u .b{background:#3b82f6;color:#fff;border-bottom-left-radius:3px}
        .m.a .b{background:#fff;color:#1f2937;border-bottom-right-radius:3px}
        .t{font-size:11px;color:#9ca3af;margin-top:6px}
        .in{padding:18px;background:#fff;display:flex;gap:12px;border-top:1px solid #e5e7eb}
        input{flex:1;padding:15px 20px;border:2px solid #e5e7eb;border-radius:25px;font-size:16px;font-family:inherit}
        input:focus{outline:none;border-color:#3b82f6}
        button{padding:15px 30px;background:#3b82f6;color:#fff;border:none;border-radius:25px;cursor:pointer;font-weight:700;font-size:16px}
        button:hover{background:#2563eb}
        button:disabled{background:#d1d5db;cursor:not-allowed}
        .loading{text-align:center;padding:15px;color:#6b7280;font-style:italic}
        .b h3{font-size:18px;margin:14px 0 10px 0;color:#1e3a8a}
        .b h4{font-size:16px;margin:12px 0 8px 0;color:#3b82f6}
        .b strong{color:#1e40af;font-weight:600}
        .b ul{margin-right:25px;margin-top:8px}
    </style>
</head>
<body>
    <div class="c">
        <div class="h">
            <h1>📚 دستیار قوانین آموزشی دانشگاه</h1>
            <p>پاسخگویی دقیق بر اساس آیین‌نامه دانشگاه آزاد اسلامی</p>
        </div>
        
        <div class="chat" id="ch">
            <div class="m a">
                <div class="b">
                    سلام! من دستیار قوانین دانشگاه هستم.<br>
                    می‌توانم درباره ثبت‌نام، واحد درسی، حضور و غیاب، مرخصی، انتقال و... کمک کنم.
                </div>
            </div>
        </div>
        
        <div class="in">
            <input id="i" placeholder="سوال خود را بپرسید..." onkeypress="if(event.key==='Enter')send()">
            <button id="btn" onclick="send()">ارسال</button>
        </div>
    </div>
    
    <script>
        function add(type,txt,time){
            const ch=document.getElementById('ch');
            const t=time?new Date(time).toLocaleTimeString('fa-IR',{hour:'2-digit',minute:'2-digit'}):'';
            let f=txt.replace(/### (.*?)\\n/g,'<h3>$1</h3>').replace(/#### (.*?)\\n/g,'<h4>$1</h4>').replace(/\\*\\*(.*?)\\*\\*/g,'<strong>$1</strong>').replace(/^- (.*)$/gm,'• $1').replace(/\\n/g,'<br>');
            ch.innerHTML+=`<div class="m ${type}"><div class="b">${f}${t?`<div class="t">${t}</div>`:''}</div></div>`;
            ch.scrollTop=ch.scrollHeight;
        }
        
        async function send(){
            const i=document.getElementById('i');
            const btn=document.getElementById('btn');
            const q=i.value.trim();
            if(q.length<3){alert('سوال باید حداقل 3 کاراکتر باشد');return}
            add('u',q,new Date().toISOString());
            i.value='';
            btn.disabled=true;
            btn.textContent='⏳';
            const ch=document.getElementById('ch');
            const lid='l'+Date.now();
            ch.innerHTML+=`<div class="loading" id="${lid}">⏳ در حال بررسی...</div>`;
            ch.scrollTop=ch.scrollHeight;
            try{
                const r=await fetch('/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
                document.getElementById(lid)?.remove();
                if(!r.ok)throw new Error('خطا');
                const d=await r.json();
                add('a',d.answer,new Date().toISOString());
            }catch(e){
                document.getElementById(lid)?.remove();
                add('a',`❌ ${e.message}`,new Date().toISOString());
            }finally{
                btn.disabled=false;
                btn.textContent='ارسال';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/ask', methods=['POST'])
def ask():
    try:
        data = request.get_json(force=True) or {}
        q = data.get('question', '').strip()
        
        if len(q) < 3:
            return jsonify({'error': 'سوال کوتاه است'}), 400
        
        async def call():
            async with AsyncCodewordsClient() as client:
                r = await client.run(
                    service_id=SERVICE_ID,
                    inputs={"question": q}
                )
                r.raise_for_status()
                return r.json()
        
        result = asyncio.run(call())
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ✅ ASGI برای Vercel
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)