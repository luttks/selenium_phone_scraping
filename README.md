# Phone Scraper Web App

Ứng dụng web scraping điện thoại từ TGDD và FPT Shop với tính năng tìm kiếm, lọc và chia sẻ kết quả qua email.

## 🚀 Tính năng

- 🔍 Tìm kiếm và lọc điện thoại theo nhiều tiêu chí (hãng, giá, RAM, bộ nhớ, độ phân giải, tần số quét)
- 📧 Tích hợp Google OAuth để lưu email và nhận kết quả qua email
- 💾 Lưu kết quả tìm kiếm vào Redis (TTL 24 giờ)
- 📤 Chia sẻ kết quả qua link trực tiếp
- 🎨 Giao diện responsive với Tailwind CSS
- ⚡ API FastAPI với background tasks

## 📋 Yêu cầu hệ thống

- Python 3.8+
- Redis Server
- Chrome Browser
- Google OAuth credentials (optional, for email features)

## 🛠️ Cài đặt

### 1. Clone repository
```bash
git clone <repository-url>
cd selenium_phone_scraping
```

### 2. Tạo virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Cài đặt Redis

#### Sử dụng Docker (khuyên dùng):
```bash
docker run -d --name phone_scraper_redis -p 6379:6379 redis:alpine
```

#### Hoặc cài đặt trực tiếp:
- Ubuntu/Debian: `sudo apt install redis-server`
- macOS: `brew install redis`
- Windows: Download từ https://redis.io/download

### 5. Cấu hình môi trường

Copy file mẫu và chỉnh sửa:

```bash
cp env.example .env
```

Sau đó chỉnh sửa file `.env` với thông tin của bạn:

```env
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379

# Email Service (tùy chọn - để sử dụng tính năng email)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
FROM_EMAIL=your-email@gmail.com
FRONTEND_URL=http://localhost:8000

# Google OAuth (tùy chọn - để sử dụng tính năng email)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### 6. Thiết lập Google OAuth (tùy chọn)

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Kích hoạt Google+ API
4. Tạo OAuth 2.0 Client ID:
   - Authorized JavaScript origins: `http://localhost:8000`
   - Authorized redirect URIs: `http://localhost:8000/auth/google/callback`
5. Copy Client ID vào file `.env`

### 7. Chạy ứng dụng

```bash
# Đảm bảo Redis đang chạy
docker start phone_scraper_redis

# Chạy ứng dụng
python main.py
```

Truy cập: http://localhost:8000

## 📖 Cách sử dụng

### Tìm kiếm cơ bản
1. Chọn hãng điện thoại (Samsung, iPhone, etc.)
2. Chọn khoảng giá
3. Điều chỉnh RAM và bộ nhớ (tùy chọn)
4. Chọn độ phân giải màn hình (tùy chọn)
5. Chọn tần số quét (tùy chọn)
6. Nhấn "Tìm kiếm"

### Nhận kết quả qua email (tùy chọn)
1. Nhấn nút "Tìm kiếm"
2. Hệ thống sẽ yêu cầu đăng nhập Google để lấy email
3. Kết quả sẽ được gửi qua email với link trực tiếp
4. Click vào link trong email để xem kết quả

### Chia sẻ kết quả
- Mỗi kết quả tìm kiếm có URL duy nhất
- Chia sẻ URL để người khác xem kết quả mà không cần tìm kiếm lại

## 🏗️ Cấu trúc dự án

```
selenium_phone_scraping/
├── main.py                    # FastAPI application
├── cache/
│   └── redis_client.py        # Redis cache utilities
├── email_service/
│   └── email_sender.py        # Email service
├── auth/
│   └── google_oauth.py        # Google OAuth utilities
├── selenium_/
│   ├── page/
│   │   ├── tgdd.py           # TGDD scraper
│   │   └── fpt.py            # FPT scraper
│   ├── model/
│   │   ├── phone_configuration.py
│   │   ├── filter_list.py
│   │   └── result.py
│   └── scraper/
│       ├── adaptive_filter_applier.py
│       ├── dynamic_filters.py
│       └── filter_scraper.py
├── templates/
│   └── index.html            # Main UI
├── static/                   # Static files
└── requirements.txt          # Python dependencies
```

## 🔧 API Endpoints

- `GET /` - Trang chủ
- `GET /{result_id}` - Xem kết quả đã lưu
- `POST /scrape` - Thực hiện scraping
- `GET /api/results/{result_id}` - API lấy kết quả
- `GET /auth/google/config` - Cấu hình Google OAuth

## 🐛 Troubleshooting

### Redis connection failed
```bash
# Kiểm tra Redis đang chạy
docker ps | grep redis

# Hoặc start Redis
docker start phone_scraper_redis
```

### Chrome driver issues
```bash
# Cập nhật Chrome driver tự động
pip install --upgrade webdriver-manager
```

### Email không gửi được
- Kiểm tra cấu hình SMTP trong `.env`
- Đảm bảo "Less secure app access" được bật (cho Gmail)
- Hoặc sử dụng App Passwords

## 📝 License

MIT License

## 🤝 Đóng góp

1. Fork project
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📞 Liên hệ

Nếu có vấn đề hoặc cần hỗ trợ, vui lòng tạo issue trên GitHub.