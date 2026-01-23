# AI Chatbot Backend

Backend API tích hợp OpenAI Function Calling để xử lý câu hỏi tự nhiên về phòng họp, query real-time từ Odoo.

## 🚀 Tech Stack

- **FastAPI** - Python web framework
- **OpenAI GPT-4** - AI chatbot với Function Calling
- **Odoo XML-RPC** - Data source
- **Pydantic** - Config & validation

## 📋 Tính năng

AI chatbot có thể tự động xử lý các câu hỏi:

- ✅ Tìm phòng họp rảnh trong khoảng thời gian
- ✅ Kiểm tra trạng thái phòng hiện tại
- ✅ Xem lịch đặt phòng
- ✅ Liệt kê tất cả phòng họp
- ✅ Xem thông tin chi tiết phòng

## 🛠️ Cài đặt

### 1. Clone và cài dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Cấu hình môi trường

```bash
cp .env.example .env
```

Chỉnh sửa file `.env` với thông tin thực tế:

```env
OPENAI_API_KEY=sk-your-actual-api-key
ODOO_URL=http://your-odoo-server:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
CORS_ORIGINS=http://localhost:3000
```

### 3. Chạy server

```bash
python -m app.main
# hoặc: uvicorn app.main:app --reload
```

Server sẽ chạy tại: **http://localhost:8000**

## 📚 API Documentation

### Swagger UI
Truy cập http://localhost:8000/docs để xem interactive API documentation

### Endpoints

#### POST /api/chat
Chat với AI chatbot

**Request:**
```json
{
  "message": "Tuần này có phòng nào rảnh không?",
  "conversation_history": []
}
```

**Response:**
```json
{
  "response": "Tuần này có 2 phòng rảnh: Phòng A (10 người), Phòng C (15 người)",
  "function_called": "search_available_rooms",
  "function_arguments": {...},
  "function_result": [...],
  "conversation_history": [...]
}
```

#### GET /api/health
Health check

**Response:**
```json
{
  "status": "healthy",
  "service": "AI Chatbot Backend",
  "version": "1.0.0"
}
```

## 🧪 Testing

### Manual Test với curl

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Có những phòng họp nào?"}'
```

### Test với Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"message": "Phòng A có rảnh không?"}
)
print(response.json())
```

## 📂 Cấu trúc dự án

```
backend/
├── .env.example          # Config template
├── .gitignore           # Git ignore
├── requirements.txt     # Dependencies
├── README.md           # File này
└── app/
    ├── __init__.py
    ├── config.py        # Pydantic Settings
    ├── main.py         # FastAPI app
    ├── routers/
    │   ├── __init__.py
    │   └── chat.py     # Chat endpoints
    └── services/
        ├── __init__.py
        ├── odoo_service.py    # Odoo integration
        └── openai_service.py  # OpenAI integration
```

## 🔧 Functions được hỗ trợ

1. **search_available_rooms** - Tìm phòng rảnh
2. **get_room_status** - Kiểm tra trạng thái phòng
3. **get_room_bookings** - Xem lịch đặt phòng
4. **get_all_rooms** - Liệt kê tất cả phòng
5. **get_room_info** - Xem thông tin chi tiết phòng

## 📌 Lưu ý

### OpenAI API Key
- Lấy API key tại: https://platform.openai.com
- Chi phí: ~$0.01-0.03 per request (GPT-4)
- Nên set budget limit

### Odoo Connection
- Cần Odoo đang chạy với module `phong_hop`
- Kiểm tra URL, database, credentials

### CORS
- Cấu hình `CORS_ORIGINS` trong `.env` để cho phép frontend gọi API

## 🔜 Next Steps (Optional)

- [ ] Thêm function `create_booking` - Đặt phòng qua chatbot
- [ ] WebSocket support - Real-time chat
- [ ] Frontend UI - Web chat interface
- [ ] Chat history - Lưu lịch sử hội thoại
- [ ] Deploy production - Docker + Nginx + SSL

## 📖 Tài liệu tham khảo

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-23
