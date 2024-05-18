# Instant STT and Translation

這個專案是一個基於 Flask 和 WebSocket 的即時語音轉錄和翻譯應用，使用 OpenAI 的 Whisper 模型來轉錄語音，並將轉錄的英文文本翻譯成繁體中文。

## 系統需求

- Python 3.8 或以上
- Redis 服務
- Flask
- Flask-SocketIO
- python-dotenv
- openai

## 安裝指南

### 創建虛擬環境

首先，確保您的系統中已安裝 Python。然後，在您的專案目錄下創建一個虛擬環境：

```bash
python -m venv venv
```

啟動虛擬環境：

在 Windows 下：

```bash
venv\Scripts\activate
```

在 Unix 或 MacOS 下：

```bash
source venv/bin/activate
```

### 安裝依賴包

安裝專案所需的所有依賴包：

```bash
pip install flask flask-socketio python-dotenv openai speech_recognition pydub requests
```

### 設定環境變數

請在專案的根目錄下創建一個名為`.env`的文件，並填入相應的環境變數，如下所示：

```plaintext
OPENAI_API_KEY=您的OpenAI API金鑰
SOCKET_IO_URL=http://localhost:5000
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

### 運行專案

在專案的根目錄下執行以下命令來啟動服務：

```bash
python app.py
```

開啟瀏覽器並訪問`http://localhost:5000`來使用這個應用。

## 功能描述

- **即時語音錄製與轉錄**：使用者可以透過網頁介面進行語音錄製，系統會即時轉錄語音為英文文本。
- **語音翻譯**：系統會將轉錄得到的英文文本翻譯成繁體中文。
- **歷史記錄**：轉錄與翻譯的結果會存儲在 Redis 資料庫中，並可以通過 WebSocket 接口實時更新到客戶端。
