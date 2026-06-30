import sqlite3
import json
import urllib.request
import urllib.parse
import time
import os

# 1. التوكن الخاص ببوتك جاهز ومحمي داخل الكود
TOKEN = "8981280860:AAGkpzGr11CetPydy8o7JytumYyWGZWD0ZQ"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

# 2. رابط الـ WebApp تم تعديله وحذف التكرار ليعمل 100%
WEBAPP_URL = "https://iraq180.github.io/Weel/"

# ---- إعداد قاعدة البيانات لحفظ الأسماء تلقائياً ----
def init_db():
    conn = sqlite3.connect("users_wheels.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS names (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id INTEGER, 
            name TEXT, 
            UNIQUE(user_id, name)
        )
    ''')
    conn.commit()
    conn.close()

def add_name(user_id, name):
    try:
        conn = sqlite3.connect("users_wheels.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO names (user_id, name) VALUES (?, ?)", (user_id, name))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user_names(user_id):
    conn = sqlite3.connect("users_wheels.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM names WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def clear_user_names(user_id):
    conn = sqlite3.connect("users_wheels.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM names WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ---- دالة الاتصال بتليجرام عبر مكتبة urllib المدمجة ----
def bot_request(method, payload):
    url = BASE_URL + method
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return {}

# ---- تشغيل وفحص الرسائل المستمر ----
def main():
    init_db()
    offset = 0
    print("🚀 البوت يعمل الآن بنجاح وعلى مدار الساعة...")
    
    while True:
        try:
            updates = bot_request("getUpdates", {"offset": offset, "timeout": 20})
            if "result" in updates and updates["result"]:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        user_id = msg["from"]["id"]
                        
                        # استقبال نتيجة اللعبة فور إغلاق الـ WebApp
                        if "web_app_data" in msg:
                            data = json.loads(msg["web_app_data"]["data"])
                            winner = data.get("winner", "غير معروف")
                            bot_request("sendMessage", {
                                "chat_id": chat_id, 
                                "text": f"🎯 توقف الدولاب الملون وعيّن النتيجة!\n\n👑 الاسم الفائز المحظوظ هو: 🎉 **{winner}** 🎉"
                            })
                            continue

                        if "text" in msg:
                            text_msg = msg["text"].strip()
                            
                            # أمر البدء
                            if text_msg == "/start":
                                text = (
                                    "🎰 أهلاً بك في بوت دولاب الأسماء الملون الاحترافي!\n\n"
                                    "⚙️ **طريقة الاستخدام من الشات:**\n"
                                    "➕ أرسل: `اضف` متبوعاً بالاسم (مثال: `اضف ضياء`)\n"
                                    "📋 لعرض قائمتك الحالية أرسل: `الاسماء`\n"
                                    "🗑️ لمسح أسماءك بالكامل أرسل: `... مسح الكل`"
                                )
                                bot_request("sendMessage", {"chat_id": chat_id, "text": text})
                            
                            # أمر إضافة اسم للجدول
                            elif text_msg.startswith("اضف "):
                                new_name = text_msg.replace("اضف ", "").strip()
                                if new_name:
                                    if add_name(user_id, new_name):
                                        bot_request("sendMessage", {"chat_id": chat_id, "text": f"✅ تم إضافة الاسم [ {new_name} ] إلى دولابك!"})
                                    else:
                                        bot_request("sendMessage", {"chat_id": chat_id, "text": "⚠️ هذا الاسم مضاف لديك بالفعل!"})
                            
                            # أمر عرض قائمة الأسماء مع زر الدولاب الملون
                            elif text_msg == "الاسماء":
                                names = get_user_names(user_id)
                                if names:
                                    # تشفير الأسماء ليمررها الرابط بأمان للـ WebApp
                                    encoded_names = urllib.parse.quote(",".join(names))
                                    full_webapp_url = f"{WEBAPP_URL}?names={encoded_names}"
                                    
                                    keyboard = {
                                        "inline_keyboard": [
                                            [{"text": "🎰 افتح الدولاب الملون وافتر 🎯", "web_app": {"url": full_webapp_url}}]
                                        ]
                                    }
                                    bot_request("sendMessage", {
                                        "chat_id": chat_id, 
                                        "text": "📋 اضغط على الزر بالأسفل ليفتح لك الدولاب الملون المخصص بأسمائك المضافة 👇", 
                                        "reply_markup": keyboard
                                    })
                                else:
                                    bot_request("sendMessage", {"chat_id": chat_id, "text": "📋 دولابك فارغ حالياً! أضف اسمين على الأقل لتتمكن من اللعب."})
                                    
                            # أمر مسح كل الأسماء للشخص نفسه
                            elif text_msg == "مسح الكل":
                                clear_user_names(user_id)
                                bot_request("sendMessage", {"chat_id": chat_id, "text": "🗑️ تم تفريغ دولابك الملون بالكامل بنجاح!"})
                                
        except Exception as e:
            time.sleep(2)

if __name__ == "__main__":
    main()
