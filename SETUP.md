# 電池 OQC 系統 - 安裝與部署指南

## 系統需求

- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Tesseract OCR
- Git

## 步驟 1: 環境準備

### 1.1 安裝 Tesseract OCR

#### macOS:
```bash
brew install tesseract
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install tesseract-ocr
```

#### Windows:
從 [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) 下載並安裝

### 1.2 安裝 PostgreSQL

#### macOS:
```bash
brew install postgresql
brew services start postgresql
```

#### Ubuntu/Debian:
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 1.3 建立資料庫
```bash
#sudo -u postgres psql
psql postgres
CREATE DATABASE battery_oqc;
CREATE USER battery_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE battery_oqc TO battery_user;
\q
```

### 1.4 取得 Anthropic API Key (可選)
如果您想使用 Claude AI 進行更精準的圖片識別：

1. 訪問 [Anthropic Console](https://console.anthropic.com/)
2. 註冊並登入帳戶
3. 建立新的 API Key
4. 複製 API Key 以供後續使用

**注意**：Claude AI 識別是可選功能，如果沒有設定 API Key，系統會自動使用傳統 OCR 方法。

## 步驟 2: Backend 設置

### 2.1 進入 backend 目錄
```bash
cd backend
```

### 2.2 建立虛擬環境
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2.3 安裝 Python 套件
```bash
pip install -r requirements.txt
```

### 2.4 設置環境變數
```bash
cp .env.example .env
```

編輯 `.env` 檔案：
```env
DATABASE_URL="postgresql://battery_user:your_password@localhost:5432/battery_oqc"
TESSERACT_CMD="/usr/local/bin/tesseract"  # 調整為您的 tesseract 路徑
DATA_PATH="../data"

# Anthropic Claude AI 設定 (可選)
# 如果設定了 ANTHROPIC_API_KEY，系統會優先使用 Claude AI 進行圖片識別
# 如果沒有設定，則使用傳統 OCR (OpenCV + Tesseract)
ANTHROPIC_API_KEY="your-anthropic-api-key-here"  # 請填入您的 Anthropic API Key
CLAUDE_MODEL="claude-3-5-sonnet-20241022"  # Claude 模型版本
```

**重要提醒**：
- 如果您有 Anthropic API Key，請填入 `ANTHROPIC_API_KEY`
- 如果沒有 API Key，請保留該欄位為空字串或註解掉
- 系統會自動偵測並選擇最佳的識別方法

### 2.5 初始化資料庫
```bash
# 安裝 Prisma CLI
pip install prisma

# 產生 Prisma 客戶端
prisma generate

# 執行資料庫遷移
prisma db push
```

### 2.6 測試 Backend
```bash
# 執行測試
python -m pytest tests/ -v

# 啟動開發伺服器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 步驟 3: Frontend 設置

### 3.1 進入 frontend 目錄
```bash
cd frontend
```

### 3.2 安裝 Node.js 套件
```bash
npm install
```

### 3.3 啟動開發伺服器
```bash
npm run dev
```

## 步驟 4: Claude AI 圖片識別設定 (可選)

### 4.1 Claude AI 功能介紹
系統支援兩種圖片識別方法：

1. **Claude AI Vision** (推薦)
   - 使用 Anthropic Claude AI 進行高精度圖片識別
   - 更準確的文字識別和理解能力
   - 需要 Anthropic API Key

2. **傳統 OCR** (預設備用)
   - 使用 OpenCV + Tesseract 進行 OCR 識別
   - 免費但準確性較低
   - 無需額外設定

### 4.2 啟用 Claude AI 識別

1. 確認您已在 `.env` 檔案中設定 `ANTHROPIC_API_KEY`
2. 重啟後端服務
3. 在前端界面中會看到「Claude AI 可用」的狀態提示

### 4.3 驗證設定
訪問系統狀態端點來確認設定：
```bash
curl http://localhost:8000/recognition-status
```

正確的回應應包含：
```json
{
  "claude_ai": {
    "service_name": "Claude AI Vision",
    "available": true,
    "model": "claude-3-5-sonnet-20241022",
    "api_key_configured": true
  },
  "preferred_method": "Claude AI"
}
```

### 4.4 識別方式對比

| 特性 | Claude AI | 傳統 OCR |
|------|-----------|----------|
| 準確性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 速度 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 成本 | 需付費 | 免費 |
| 複雜圖片處理 | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 多語言支援 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 步驟 5: 系統測試

### 5.1 執行完整測試
```bash
# 在專案根目錄執行
python run_tests.py
```

### 5.2 手動測試流程

1. 打開瀏覽器訪問 http://localhost:3000
2. 檢查識別服務狀態（頁面頂部藍色狀態欄）
3. 確保 data 資料夾中有電池圖片
4. 點擊「處理圖片」按鈕
5. 觀察使用的識別方法（Claude AI 或 Traditional OCR）
6. 檢視處理結果，查看「識別方式」欄位
7. 點擊「儲存到資料庫」
8. 訪問「電池資料」頁面檢視儲存的資料
9. 測試「匯出 CSV」功能

**Claude AI 測試要點**：
- 如果設定了 API Key，應顯示「Claude AI 可用」
- 處理圖片時會顯示「使用 Claude AI 分析圖片...」
- 結果表格中識別方式會顯示「🤖 Claude AI」
- 如果 API Key 無效，系統會自動回退至傳統 OCR

## 步驟 6: 生產部署

### 6.1 Backend 生產部署

#### 使用 Docker (推薦)
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t battery-oqc-backend .
docker run -p 8000:8000 battery-oqc-backend
```

#### 使用 systemd service
建立 `/etc/systemd/system/battery-oqc-backend.service`:
```ini
[Unit]
Description=Battery OQC Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/battery_OQC_1/backend
Environment=PATH=/path/to/battery_OQC_1/backend/venv/bin
ExecStart=/path/to/battery_OQC_1/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable battery-oqc-backend
sudo systemctl start battery-oqc-backend
```

### 6.2 Frontend 生產部署

```bash
cd frontend
npm run build
npm start
```

或使用 Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000/;
    }
}
```

## 步驟 7: 維護與監控

### 7.1 日誌檢視
```bash
# Backend 日誌
journalctl -u battery-oqc-backend -f

# 應用程式日誌
tail -f /var/log/battery-oqc/app.log
```

### 7.2 資料庫備份
```bash
# 建立備份
pg_dump battery_oqc > backup_$(date +%Y%m%d_%H%M%S).sql

# 還原備份
psql battery_oqc < backup_20240101_120000.sql
```

### 7.3 系統監控
建議使用以下工具監控系統：
- Prometheus + Grafana
- New Relic
- DataDog

## 常見問題排除

### Q1: Tesseract 找不到
```bash
# 檢查 tesseract 位置
which tesseract

# 更新 .env 檔案中的 TESSERACT_CMD
```

### Q2: 資料庫連接失敗
```bash
# 檢查資料庫狀態
sudo systemctl status postgresql

# 檢查連接
psql -h localhost -U battery_user -d battery_oqc
```

### Q3: 圖片處理失敗
```bash
# 檢查 OpenCV 安裝
python -c "import cv2; print(cv2.__version__)"

# 重新安裝
pip uninstall opencv-python
pip install opencv-python
```

### Q4: 前端 API 調用失敗
檢查 CORS 設置和代理設定：
```javascript
// next.config.js
async rewrites() {
    return [
        {
            source: '/api/:path*',
            destination: 'http://localhost:8000/:path*',
        },
    ];
}
```

### Q5: Claude AI 識別不工作
```bash
# 檢查 API Key 設定
curl -H "Authorization: Bearer your-api-key" https://api.anthropic.com/v1/messages

# 檢查後端日誌
tail -f backend.log | grep "Claude"

# 驗證環境變數
echo $ANTHROPIC_API_KEY
```

### Q6: Claude AI 成本考量
- Claude AI 按 token 數量計費
- 每張圖片約消耗 1000-2000 tokens
- 建議設定使用限制或預算警告
- 可在高峰時段使用 OCR 備用方案

## 效能優化建議

1. **資料庫索引**：為常查詢欄位建立索引
2. **圖片快取**：實現處理過圖片的快取機制
3. **批次處理**：大量圖片時使用異步處理
4. **CDN**：靜態資源使用 CDN 加速
5. **資料庫連接池**：配置適當的連接池大小

## 安全性建議

1. **環境變數**：敏感資訊使用環境變數
2. **HTTPS**：生產環境強制使用 HTTPS
3. **API 限流**：實現 API 請求限流
4. **輸入驗證**：嚴格驗證所有輸入
5. **定期備份**：建立自動化備份機制