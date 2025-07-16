FROM python:3.12-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip 並複製需求檔案
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip

# 安裝 Python 依賴
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

# 複製應用程式
COPY . .

# 暴露端口
EXPOSE 5000

# 啟動命令
CMD ["python", "app.py"]