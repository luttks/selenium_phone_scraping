# Phone Scraper (FastAPI + Selenium)

## Yêu cầu

- Python 3.13 (khuyến nghị dùng pyenv)
- Google Chrome + chromedriver (webdriver-manager sẽ tự cài)
- Docker (để chạy Redis nhanh)

## Thiết lập nhanh

```bash
# 1) Tạo và kích hoạt venv
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2) Cài dependencies
pip install -r requirements.txt

# 3) Khởi động Redis qua docker-compose
docker compose up -d redis

# 4) (Tuỳ chọn) Cấu hình môi trường
# Tạo file .env nếu cần override
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0

# 5) Chạy API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Mở `http://localhost:8000/` để vào giao diện.
- Endpoint trả về cache theo id: `GET /api/{result_id}`.

## Ghi chú

- Selenium chạy headless và chặn prompt xin quyền (notifications, camera, mic, geolocation).
- TGDD và FPT scrape song song bằng 2 phiên Chrome độc lập.

## Push lên GitHub

```bash
git init
git add .
git commit -m "init project"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
