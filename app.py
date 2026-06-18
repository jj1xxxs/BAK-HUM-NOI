import os
import re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from deep_translator import GoogleTranslator

app = Flask(__name__)

# ดึงค่าจาก Environment Variables ของ Railway
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    
    # ตรวจจับภาษาจากข้อความที่พิมพ์มา
    has_thai = re.search(r'[\u0E00-\u0E7F]', text)
    has_korean = re.search(r'[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]', text)
    
    translated_text = ""
    
    try:
        if has_thai and not has_korean:
            # ถ้าพิมพ์ไทย -> แปลเป็นเกาหลี
            translated_text = GoogleTranslator(source='th', target='ko').translate(text)
        elif has_korean and not has_thai:
            # ถ้าพิมพ์เกาหลี -> แปลเป็นไทย
            translated_text = GoogleTranslator(source='ko', target='th').translate(text)
        else:
            # ถ้าเป็นภาษาอื่น (เช่น อังกฤษล้วน หรือมีทั้งไทยและเกาหลีปนกัน) ให้ข้ามไป ไม่ต้องตอบกลับ
            return
            
        if translated_text:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=translated_text)
            )
    except Exception as e:
        print("Translation Error:", e)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

