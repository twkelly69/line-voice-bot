from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import speech_recognition as sr
import tempfile
import requests
from datetime import datetime

app = Flask(__name__)

# LINE Bot 設定
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

# 儲存使用者對話記錄
user_conversations = {}

# Google Sheets 設定
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

def setup_google_sheets():
    try:
        # 嘗試從環境變數讀取 Base64 編碼的憑證
        credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
        if credentials_base64:
            import base64
            import json
            # 解碼 Base64 並解析 JSON
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPE)
        else:
            # 嘗試從環境變數讀取 JSON 內容
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                import json
                credentials_dict = json.loads(credentials_json)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPE)
            else:
                # 本地開發時從檔案讀取
                creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', SCOPE)
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(os.environ.get('GOOGLE_SHEET_ID')).sheet1
        return sheet
    except Exception as e:
        print(f"Google Sheets 設定錯誤: {e}")
        return None

def speech_to_text(audio_url):
    try:
        # 下載音訊檔案
        response = requests.get(audio_url, headers={'Authorization': f'Bearer {os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")}'})
        
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        # 語音轉文字
        r = sr.Recognizer()
        with sr.AudioFile(temp_file_path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language='zh-TW')
        
        os.unlink(temp_file_path)
        return text
    except Exception as e:
        print(f"語音轉文字錯誤: {e}")
        return None

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
def handle_text_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    
    if user_message == '/save':
        # 儲存到 Google Sheets
        if user_id in user_conversations:
            sheet = setup_google_sheets()
            if sheet:
                try:
                    conversation = user_conversations[user_id]
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sheet.append_row([timestamp, user_id, conversation])
                    
                    # 清空對話記錄
                    user_conversations[user_id] = ""
                    
                    reply_message = "✅ 對話記錄已儲存到 Google Sheets！"
                except Exception as e:
                    reply_message = f"❌ 儲存失敗: {str(e)}"
            else:
                reply_message = "❌ Google Sheets 連接失敗"
        else:
            reply_message = "📝 目前沒有對話記錄"
    else:
        # 累積對話記錄
        if user_id not in user_conversations:
            user_conversations[user_id] = ""
        
        user_conversations[user_id] += user_message + "\n"
        reply_message = f"📝 目前對話記錄:\n{user_conversations[user_id]}"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    user_id = event.source.user_id
    
    # 取得音訊檔案 URL
    message_content = line_bot_api.get_message_content(event.message.id)
    audio_url = f"https://api-data.line.me/v2/bot/message/{event.message.id}/content"
    
    # 語音轉文字
    text = speech_to_text(audio_url)
    
    if text:
        # 累積對話記錄
        if user_id not in user_conversations:
            user_conversations[user_id] = ""
        
        user_conversations[user_id] += text + "\n"
        reply_message = f"🎤 語音轉文字: {text}\n\n📝 目前對話記錄:\n{user_conversations[user_id]}"
    else:
        reply_message = "❌ 語音轉文字失敗，請重試"
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)