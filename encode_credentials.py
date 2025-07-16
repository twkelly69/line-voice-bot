import base64
import json

# 讀取 credentials.json
try:
    with open('credentials.json', 'r', encoding='utf-8') as f:
        credentials = f.read()
    
    # 轉換為 Base64
    credentials_base64 = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    
    print("GOOGLE_CREDENTIALS_BASE64 =")
    print(credentials_base64)
    
    # 驗證可以正確解碼
    decoded = base64.b64decode(credentials_base64).decode('utf-8')
    json.loads(decoded)  # 確保是有效的 JSON
    print("\n✅ 編碼成功！可以使用此 Base64 字串")
    
except FileNotFoundError:
    print("❌ 找不到 credentials.json 檔案")
    print("請確認檔案在同一目錄下")
except json.JSONDecodeError:
    print("❌ credentials.json 格式不正確")
except Exception as e:
    print(f"❌ 發生錯誤: {e}")