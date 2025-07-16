FROM python:3.12-slim

WORKDIR /app

# 複製最小需求檔案
COPY requirements_minimal.txt .

# 安裝最小依賴
RUN pip install --no-cache-dir -r requirements_minimal.txt

# 複製應用程式
COPY app_minimal.py .

# 暴露端口
EXPOSE $PORT

# 啟動命令
CMD python app_minimal.py