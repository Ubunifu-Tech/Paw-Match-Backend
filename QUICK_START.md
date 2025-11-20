# 🚀 PawMatch Backend - Quick Start

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Setup Database
```bash
alembic upgrade head
```

### 4. Start Server
```bash
uvicorn app.main:app --reload
```

### 5. Test
```bash
python3 test_complete_workflow.py
```

✅ **Server running at:** `http://localhost:8000`  
✅ **API docs at:** `http://localhost:8000/docs`

---

## 📚 Need More Help?

- **Installation Issues?** → See [README.md](README.md)
- **Deployment?** → See [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md)
- **Frontend Integration?** → See [docs/FRONTEND_INTEGRATION_GUIDE.md](docs/FRONTEND_INTEGRATION_GUIDE.md)
- **Security Questions?** → See [docs/SECURITY.md](docs/SECURITY.md)
- **Complete Workflow?** → See [docs/APPLICATION_WORKFLOW.md](docs/APPLICATION_WORKFLOW.md)

---

## 🔑 Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users/register` | POST | Register new user |
| `/api/users/token` | POST | Login (get JWT) |
| `/api/chat/message` | POST | Send chat message |
| `/api/recommendations/{session_id}` | GET | Get breed matches |
| `/api/video/generate` | POST | Generate video |

**All endpoints:** `http://localhost:8000/docs`

---

## ✅ Production Checklist

- [ ] Generate new `SECRET_KEY` (`openssl rand -hex 32`)
- [ ] Set `DEBUG=False`
- [ ] Configure `FRONTEND_URL`
- [ ] Run all tests (`python3 test_complete_workflow.py`)
- [ ] Deploy to Railway (see [docs/RAILWAY_DEPLOYMENT.md](docs/RAILWAY_DEPLOYMENT.md))

---

**Full documentation:** [docs/README.md](docs/README.md)
