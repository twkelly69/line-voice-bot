from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioMessage
import os
import json
import tempfile
import requests
from datetime import datetime

# 嘗試導入可選的套件
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("Google Sheets 相關套件未安裝")

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("語音識別相關套件未安裝")

app = Flask(__name__)

# LINE Bot 設定
line_bot_api = LineBotApi(os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', 'dummy_token'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET', 'dummy_secret'))

# 儲存使用者對話記錄
user_conversations = {}

# Google Sheets 設定
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

def setup_google_sheets():
    if not GOOGLE_SHEETS_AVAILABLE:
        print("Google Sheets 功能不可用")
        return None
        
    try:
        # 嘗試從環境變數讀取 Base64 編碼的憑證
        credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
        if credentials_base64:
            import base64
            # 解碼 Base64 並解析 JSON
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
            credentials_dict = json.loads(credentials_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPE)
        else:
            # 嘗試從環境變數讀取 JSON 內容
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
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

def speech_to_text(message_content):
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("語音識別功能不可用")
        return "語音識別功能暫時不可用"
        
    try:
        # 將音訊內容轉換為音訊檔案
        audio_data = message_content.content
        
        # 暫存音訊檔案
        with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # 轉換為 wav 格式
        audio = AudioSegment.from_file(temp_file_path)
        wav_path = temp_file_path.replace('.m4a', '.wav')
        audio.export(wav_path, format='wav')
        
        # 語音轉文字
        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
            text = r.recognize_google(audio_data, language='zh-TW')
        
        # 清理暫存檔案
        os.unlink(temp_file_path)
        os.unlink(wav_path)
        
        return text
    except Exception as e:
        print(f"語音轉文字錯誤: {e}")
        return "語音轉文字失敗"

@app.route("/", methods=['GET'])
def health_check():
    return "LINE Bot is running!", 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature")
        abort(400)
    except Exception as e:
        print(f"處理 webhook 錯誤: {e}")
        abort(500)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    user_message = event.message.text
    
    try:
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
                        print(f"儲存到 Google Sheets 錯誤: {e}")
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
        
    except Exception as e:
        print(f"處理文字訊息錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 訊息處理失敗，請重試")
        )

@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    user_id = event.source.user_id
    
    try:
        # 取得音訊檔案內容
        message_content = line_bot_api.get_message_content(event.message.id)
        
        # 語音轉文字
        text = speech_to_text(message_content)
        
        if text and text != "語音識別功能暫時不可用" and text != "語音轉文字失敗":
            # 累積對話記錄
            if user_id not in user_conversations:
                user_conversations[user_id] = ""
            
            user_conversations[user_id] += text + "\n"
            reply_message = f"🎤 語音轉文字: {text}\n\n📝 目前對話記錄:\n{user_conversations[user_id]}"
        else:
            reply_message = f"❌ {text}"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )
        
    except Exception as e:
        print(f"處理語音訊息錯誤: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="❌ 語音處理失敗，請重試")
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)