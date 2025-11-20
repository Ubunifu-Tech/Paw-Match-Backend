# Railway Deployment Checklist

## ✅ Pre-Deployment Tests Completed

### Backend Tests
- ✅ Python 3.13 compatible
- ✅ All dependencies install successfully
- ✅ FastAPI app imports without errors
- ✅ Database URL validator handles Railway postgres:// format
- ✅ Alembic migrations present and ready
- ✅ nixpacks.toml configured correctly
- ✅ railway.toml configured correctly
- ✅ Procfile configured correctly

### Configuration Files
- ✅ `nixpacks.toml` - Python 3.11, PostgreSQL, GCC
- ✅ `railway.toml` - NIXPACKS builder, auto-migrations
- ✅ `Procfile` - Uvicorn start command
- ✅ `.env.example` - Documents all required environment variables

## 🚀 Railway Deployment Steps

### 1. Create Backend Service
1. Go to Railway Dashboard → New Project
2. Click "Deploy from GitHub repo"
3. Select `Paw-Match-Backend`
4. Service will auto-deploy (no Root Directory needed!)

### 2. Add PostgreSQL Database
1. In your Railway project → Add Service → Database → PostgreSQL
2. Railway will automatically create `DATABASE_URL` variable
3. No manual configuration needed!

### 3. Add Redis Database
1. In your Railway project → Add Service → Database → Redis
2. Railway will automatically create `REDIS_URL` variable

### 4. Configure Backend Environment Variables
Go to Backend service → Variables tab and add:

**Required:**
- `GEMINI_API_KEY` = Your Google Gemini API key
- `SECRET_KEY` = Generate with: `openssl rand -hex 32`

**Auto-configured by Railway:**
- `DATABASE_URL` = Reference: `${{PostgreSQL.DATABASE_URL}}`
- `REDIS_URL` = Reference: `${{Redis.REDIS_URL}}`

**To be set after frontend deploys:**
- `FRONTEND_URL` = `https://your-frontend.up.railway.app`

### 5. Deploy Frontend Service
1. Railway Dashboard → New Project (or add to same project)
2. Click "Deploy from GitHub repo"
3. Select `Paw-Match-Frontend`

### 6. Configure Frontend Environment Variables
Go to Frontend service → Variables tab and add:
- `NEXT_PUBLIC_API_URL` = `https://your-backend.up.railway.app`

### 7. Update Backend FRONTEND_URL
1. Copy your frontend's Railway URL
2. Go to Backend service → Variables
3. Update `FRONTEND_URL` to your frontend's URL
4. Redeploy backend service

## ⚠️ Important Notes

### Database Migrations
- Migrations run automatically on startup (configured in railway.toml)
- First deployment will take ~30-60 seconds to run all migrations
- Check logs for migration status: `alembic upgrade head`

### CORS Configuration
- Backend allows `FRONTEND_URL` and `http://localhost:3000`
- Update `FRONTEND_URL` after frontend deploys
- Must be exact URL (no trailing slash)

### Secrets Management
- Never commit `.env` files
- Use Railway's Variables feature for all secrets
- Reference other services: `${{ServiceName.VARIABLE}}`

### Health Check
Once deployed, test:
- Backend: `https://your-backend.up.railway.app/health`
- Frontend: `https://your-frontend.up.railway.app`

## 🐛 Troubleshooting

### Backend won't start
- Check logs for missing environment variables
- Verify `GEMINI_API_KEY` and `SECRET_KEY` are set
- Check database connection: `DATABASE_URL` should start with `postgresql+asyncpg://`

### Database connection fails
- Railway auto-converts `postgres://` to `postgresql+asyncpg://`
- Check config.py field_validator is working
- Verify PostgreSQL service is running

### Frontend can't reach backend
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify CORS: `FRONTEND_URL` must match frontend Railway URL
- Test backend `/health` endpoint directly

### Migrations fail
- Check PostgreSQL service is running
- View logs: Railway dashboard → Backend service → Logs
- Manually run: `python3 -m alembic upgrade head`

## 📊 Post-Deployment Verification

1. ✅ Backend /health endpoint returns 200
2. ✅ Frontend loads without errors
3. ✅ Frontend can call backend API
4. ✅ Database migrations completed
5. ✅ Redis connection working
6. ✅ User registration/login works
7. ✅ AI chat functionality works
8. ✅ Breed search/filtering works

## 🔧 Environment Variables Summary

### Backend (Required)
```env
GEMINI_API_KEY=sk-...
SECRET_KEY=32_character_hex_string
DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
FRONTEND_URL=https://your-frontend.up.railway.app
```

### Frontend (Required)
```env
NEXT_PUBLIC_API_URL=https://your-backend.up.railway.app
```

## 📝 Deployment Complete!

Your Paw Match app should now be live on Railway! 🎉
