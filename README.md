# LINE 語音機器人

一個支援語音轉文字並累積對話記錄的 LINE 機器人，可將對話記錄儲存到 Google Sheets。

## 功能特色

- 🎤 語音轉文字功能
- 📝 對話記錄累積
- 💾 使用 `/save` 儲存到 Google Sheets
- 🔄 即時回覆對話記錄

## 安裝與設定

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 環境變數設定

複製 `.env.example` 為 `.env` 並填入相關資訊：

```bash
cp .env.example .env
```

設定以下環境變數：
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot 存取權杖
- `LINE_CHANNEL_SECRET`: LINE Bot 通道密鑰
- `GOOGLE_SHEET_ID`: Google Sheets 文件 ID

### 3. Google Sheets API 設定

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇既有專案
3. 啟用 Google Sheets API 和 Google Drive API
4. 建立服務帳戶並下載 JSON 金鑰檔案
5. 將金鑰檔案重新命名為 `credentials.json` 並放在專案根目錄

### 4. 執行應用程式

```bash
python app.py
```

## 使用方法

1. 在 LINE 中傳送語音訊息或文字訊息
2. 機器人會累積所有對話記錄
3. 輸入 `/save` 將對話記錄儲存到 Google Sheets
4. 儲存後對話記錄會清空，重新開始累積

## Google Sheets 格式

儲存的資料包含：
- 時間戳記
- 使用者 ID
- 對話記錄內容