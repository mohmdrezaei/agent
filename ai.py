from flask import Flask, request, jsonify, render_template_string
import requests
import json

app = Flask(__name__)

# ✅ تنظیمات
API_KEY = 'cwk-95bb46cd9f296a1e4915e805bc2cfb5572d4cec2587235f8cb178846b64f9e13'
SERVICE_ID = "university_rules_assistant_47c12da2"
BASE_URL = "https://runtime.codewords.ai"

def call_codewords_api(question: str):
    """فراخوانی CodeWords با requests"""
    try:
        response = requests.post(
            f"{BASE_URL}/run/{SERVICE_ID}",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={"question": question.strip()},
            timeout=60
        )
        
        if response.status_code >= 400:
            try:
                error_detail = response.json().get("detail", response.text)
            except:
                error_detail = response.text
            raise Exception(f"خطا: {error_detail}")
        
        return response.json()
        
    except requests.Timeout:
        raise Exception("زمان انتظار تمام شد")
    except requests.ConnectionError:
        raise Exception("خطا در اتصال")

HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>دستیار قوانین دانشگاه</title>
    <style>
        :root{--p:#1e3a8a;--l:#3b82f6}
        *{margin:0;padding:0;box-sizing:border-box;font-family:Tahoma,Arial}
        body{background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:10px}
        .box{width:100%;max-width:850px;background:white;border-radius:20px;overflow:hidden;box-shadow:0 20px 50px rgba(0,0,0,0.3)}
        .h{background:var(--p);color:white;padding:20px;text-align:center}
        .h h1{font-size:22px;margin-bottom:5px}
        .h p{font-size:13px;opacity:0.9}
        .m{padding:20px;overflow-y:auto;background:#f3f4f6;min-height:500px;max-height:600px}
        .msg{margin:12px 0;display:flex;animation:f 0.4s}
        .u{justify-content:flex-start}
        .b{justify-content:flex-end}
        .bub{max-width:78%;padding:14px 18px;border-radius:18px;line-height:1.6;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
        .u .bub{background:var(--l);color:white;border-bottom-left-radius:4px}
        .b .bub{background:white;color:#1f2937;border-bottom-right-radius:4px}
        .t{font-size:10px;color:#888;margin-top:5px}
        .in{padding:15px;background:#fff;display:flex;gap:10px;border-top:1px solid #e5e7eb}
        input{flex:1;padding:16px;border:2px solid #e5e7eb;border-radius:30px;font-size:15px}
        input:focus{outline:none;border-color:var(--p)}
        button{padding:16px 28px;background:var(--p);color:white;border:none;border-radius:30px;cursor:pointer;font-weight:bold}
        button:hover{background:#1e40af}
        button:disabled{background:#d1d5db}
        @keyframes f{from{opacity:0;transform:translateY(10px)}to{opacity:1}}
        .loading{text-align:center;padding:15px;color:#6b7280;font-style:italic}
        .bub h3{font-size:18px;margin:12px 0 8px;color:var(--p)}
        .bub h4{font-size:16px;margin:10px 0 6px;color:var(--l)}
        .bub strong{color:var(--p)}
    </style>
</head>
<body>
<div class="box">
    <div class="h">
        <h1>📚 دستیار قوانین آموزشی دانشگاه</h1>
        <p>پاسخگویی بر اساس آیین‌نامه رسمی دانشگاه آزاد اسلامی</p>
    </div>
    <div class="m" id="m">
        <div class="msg b"><div class="bub">سلام! سوال خود درباره قوانین دانشگاه را بپرسید.</div></div>
    </div>
    <div class="in">
        <input type="text" id="q" placeholder="مثال: شرایط ثبت‌نام چیست؟" autocomplete="off">
        <button onclick="send()">ارسال</button>
    </div>
</div>

<script>
    const m=document.getElementById('m');
    function add(t,s='b',time=new Date().toLocaleTimeString('fa-IR',{hour:'2-digit',minute:'2-digit'})){
        let f=t.replace(/### (.*?)\\n/g,'<h3>$1</h3>').replace(/#### (.*?)\\n/g,'<h4>$1</h4>').replace(/\\*\\*(.*?)\\*\\*/g,'<strong>$1</strong>').replace(/^- (.*)$/gm,'• $1').replace(/\\n/g,'<br>');
        const d=document.createElement('div');
        d.className=`msg ${s==='u'?'u':'b'}`;
        d.innerHTML=`<div class="bub">${f}<div class="t">${time}</div></div>`;
        m.appendChild(d);m.scrollTop=m.scrollHeight;
    }
    async function send(){
        const i=document.getElementById('q');
        const q=i.value.trim();if(!q||q.length<3){alert('سوال باید حداقل 3 کاراکتر باشد');return;}
        add(q,'u');i.value='';
        const b=document.querySelector('button');b.disabled=true;b.textContent='⏳';
        const lid='l'+Date.now();
        m.innerHTML+=`<div class="loading" id="${lid}">⏳ در حال بررسی...</div>`;
        m.scrollTop=m.scrollHeight;
        try{
            const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q})});
            document.getElementById(lid)?.remove();
            const d=await r.json();
            if(d.error)throw new Error(d.error);
            add(d.answer||"بدون پاسخ");
        }catch(e){document.getElementById(lid)?.remove();add("❌ "+e.message,'b');}
        finally{b.disabled=false;b.textContent='ارسال';}
    }
    document.getElementById('q').addEventListener('keypress',e=>e.key==='Enter'&&send());
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json(force=True) or {}
        q = data.get("question", "").strip()
        
        if len(q) < 3:
            return jsonify({"error": "سوال خیلی کوتاه است"}), 400
        
        # فراخوانی CodeWords
        result = call_codewords_api(q)
        
        return jsonify({"answer": result.get("answer", "پاسخی دریافت نشد")})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ ASGI wrapper برای Vercel
from asgiref.wsgi import WsgiToAsgi
application = WsgiToAsgi(app)

# برای لوکال
if __name__ == "__main__":
    print("🚀 سرور در حال اجرا...")
    print("🌐 http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)