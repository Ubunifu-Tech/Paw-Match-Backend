# Railway Deployment Guide - PawMatch Backend

## 🚂 Why Railway?

Railway provides:
- ✅ **PostgreSQL Database Hosting** (built-in)
- ✅ **Automatic HTTPS/SSL**
- ✅ **Environment Variable Management**
- ✅ **GitHub Integration** (auto-deploy on push)
- ✅ **Easy Scaling**
- ✅ **Free Tier Available** ($5 credit/month)

---

## 📋 Pre-Deployment Checklist

### 1. **Ensure All Files Are Ready**
- [x] `requirements.txt` with all dependencies
- [x] Database migrations in `alembic/versions/`
- [x] `.env.example` for reference
- [x] `Procfile` or Railway will auto-detect FastAPI

### 2. **Generate Production SECRET_KEY**
```bash
openssl rand -hex 32
```
**Save this key** - you'll add it to Railway environment variables.

### 3. **Verify Database Models**
Ensure all migrations are created:
```bash
cd backend
alembic revision --autogenerate -m "final migration check"
alembic upgrade head
```

---

## 🚀 Step-by-Step Deployment

### **Step 1: Create Railway Account**

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended for auto-deploy)
3. Verify your email

### **Step 2: Create New Project**

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Connect your GitHub account
4. Select your `dog-breed` repository
5. Railway will detect it's a Python app

### **Step 3: Add PostgreSQL Database**

1. In your project dashboard, click **"New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create a PostgreSQL instance
4. Database credentials are auto-generated

### **Step 4: Configure Environment Variables**

In your Railway project:

1. Go to **"Variables"** tab
2. Add the following variables:

#### **Required Variables:**
```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Database (Railway auto-provides DATABASE_URL)
# You may need to modify it for asyncpg:
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Security - CRITICAL!
SECRET_KEY=<your_generated_secret_from_step_2>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS - Set to your frontend URL
FRONTEND_URL=https://your-frontend-domain.com

# Optional
DEBUG=False
REDIS_URL=redis://localhost:6379/0  # If using Redis
```

#### **Database URL Format**
Railway provides `DATABASE_URL` in format:
```
postgresql://user:pass@host:port/db
```

You need to convert it to asyncpg format:
```
postgresql+asyncpg://user:pass@host:port/db
```

**Option 1: Manual Conversion**
Copy the Railway `DATABASE_URL` and add `+asyncpg` after `postgresql`.

**Option 2: Auto-Conversion in Code**
Add this to `app/core/config.py`:
```python
@property
def database_url(self) -> str:
    """Convert Railway DATABASE_URL to asyncpg format"""
    url = os.getenv("DATABASE_URL", self._database_url)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url
```

### **Step 5: Configure Build Settings**

Railway should auto-detect, but verify:

1. **Build Command**: (auto-detected)
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Command**: Create a `Procfile` in backend root:
   ```
   web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

   Or set in Railway dashboard:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Root Directory**: Set to `backend` if your repo has multiple folders

### **Step 6: Run Database Migrations**

After first deployment:

1. Go to Railway project → **"Settings"** → **"Service"**
2. Under **"Deploy"**, add a **"Deploy Command"**:
   ```bash
   alembic upgrade head
   ```

Or run manually via Railway CLI:
```bash
railway run alembic upgrade head
```

### **Step 7: Deploy**

1. Click **"Deploy"**
2. Railway will:
   - Install dependencies
   - Run migrations
   - Start the application
3. Monitor logs in the **"Deployments"** tab

### **Step 8: Get Your URL**

1. Go to **"Settings"** → **"Networking"**
2. Click **"Generate Domain"**
3. Railway provides: `your-app.up.railway.app`
4. (Optional) Add custom domain

---

## 🔧 Railway CLI Setup (Optional)

For easier management:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run commands in Railway environment
railway run alembic upgrade head

# View logs
railway logs

# Open project in browser
railway open
```

---

## 📝 Post-Deployment Configuration

### **1. Update CORS Settings**

Ensure your frontend URL is in `FRONTEND_URL` environment variable.

In `app/main.py`, verify CORS is configured:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### **2. Test API Endpoints**

```bash
# Health check
curl https://your-app.up.railway.app/

# API docs
https://your-app.up.railway.app/docs

# Test registration
curl -X POST https://your-app.up.railway.app/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"Test","password":"Test1234"}'
```

### **3. Monitor Application**

Railway provides:
- **Logs**: Real-time application logs
- **Metrics**: CPU, Memory, Network usage
- **Deployments**: History of all deployments

---

## 🔐 Security Best Practices for Production

### **1. Environment Variables**
- ✅ Never commit `.env` to GitHub
- ✅ Use Railway's environment variables
- ✅ Different `SECRET_KEY` for production
- ✅ Set `DEBUG=False`

### **2. Database Security**
- ✅ Railway PostgreSQL is private by default
- ✅ Use strong passwords (auto-generated)
- ✅ Enable SSL connections
- ✅ Regular backups (Railway provides)

### **3. API Security**
- ✅ HTTPS enabled by default on Railway
- ✅ Set proper CORS origins
- ✅ Rate limiting configured
- ✅ JWT tokens with expiration

### **4. Secrets Management**
```bash
# Add secrets via Railway CLI
railway variables set SECRET_KEY=your_secret_here
railway variables set GEMINI_API_KEY=your_key_here
```

---

## 📊 Database Management

### **Access Railway PostgreSQL**

**Option 1: Railway Dashboard**
1. Click on PostgreSQL service
2. Go to **"Data"** tab
3. Use built-in query editor

**Option 2: Connect Locally**
```bash
# Get connection string from Railway
railway variables

# Connect with psql
psql postgresql://user:pass@host:port/db

# Or use GUI tool (TablePlus, pgAdmin, etc.)
```

### **Run Migrations**
```bash
# Via Railway CLI
railway run alembic upgrade head

# Rollback
railway run alembic downgrade -1

# Check current version
railway run alembic current
```

### **Database Backups**
Railway provides automatic backups:
- Go to PostgreSQL service
- **"Backups"** tab
- Download or restore

---

## 🔄 Continuous Deployment

### **Auto-Deploy on Git Push**

Railway automatically deploys when you push to GitHub:

1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update API"
   git push origin main
   ```
3. Railway detects the push
4. Automatically builds and deploys
5. Monitor in **"Deployments"** tab

### **Deploy Specific Branch**

1. Go to **"Settings"** → **"Service"**
2. Under **"Source"**, select branch
3. Railway will deploy from that branch

---

## 🐛 Troubleshooting

### **Issue: Database Connection Error**

**Solution:**
```bash
# Check DATABASE_URL format
railway variables | grep DATABASE_URL

# Ensure it's converted to asyncpg format
# Should be: postgresql+asyncpg://...
```

### **Issue: Migrations Not Running**

**Solution:**
```bash
# Manually run migrations
railway run alembic upgrade head

# Check migration status
railway run alembic current
```

### **Issue: Module Not Found**

**Solution:**
```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Commit and push
git add requirements.txt
git commit -m "Update dependencies"
git push
```

### **Issue: Port Binding Error**

**Solution:**
Ensure your start command uses `$PORT`:
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### **Issue: CORS Errors**

**Solution:**
```bash
# Update FRONTEND_URL in Railway variables
railway variables set FRONTEND_URL=https://your-frontend.com

# Restart deployment
railway up
```

---

## 💰 Pricing & Limits

### **Free Tier**
- $5 credit per month
- Enough for small projects
- Includes PostgreSQL

### **Paid Plans**
- **Hobby**: $5/month
- **Pro**: $20/month
- **Enterprise**: Custom

### **Resource Limits**
- **Memory**: 512MB - 8GB
- **CPU**: Shared - Dedicated
- **Storage**: 1GB - 100GB

Monitor usage in **"Usage"** tab.

---

## 📱 Frontend Deployment

### **Deploy Frontend to Vercel/Netlify**

Update frontend environment variables:
```env
REACT_APP_API_URL=https://your-app.up.railway.app
```

### **Deploy Frontend to Railway**

You can also deploy frontend on Railway:
1. Create new Railway service
2. Connect frontend repo
3. Railway auto-detects React/Next.js
4. Set environment variables
5. Deploy

---

## 🔍 Monitoring & Logs

### **View Logs**
```bash
# Via CLI
railway logs

# Via Dashboard
Go to "Deployments" → Select deployment → "Logs"
```

### **Set Up Alerts**
1. Go to **"Settings"** → **"Notifications"**
2. Add webhook or email
3. Get notified on deployment failures

### **Health Checks**
Add a health endpoint in `app/main.py`:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}
```

Monitor at: `https://your-app.up.railway.app/health`

---

## 🚀 Production Checklist

Before going live:

- [ ] `SECRET_KEY` is strong and unique
- [ ] `DEBUG=False`
- [ ] `FRONTEND_URL` set to production domain
- [ ] Database migrations applied
- [ ] CORS configured correctly
- [ ] HTTPS enabled (automatic on Railway)
- [ ] API documentation disabled or protected
- [ ] Rate limiting configured
- [ ] Monitoring set up
- [ ] Backups enabled
- [ ] Error tracking configured (Sentry, etc.)
- [ ] Load testing completed
- [ ] Security audit passed

---

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway CLI Reference](https://docs.railway.app/develop/cli)
- [PostgreSQL on Railway](https://docs.railway.app/databases/postgresql)
- [Environment Variables](https://docs.railway.app/develop/variables)
- [Custom Domains](https://docs.railway.app/deploy/exposing-your-app)

---

## 🆘 Support

- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Railway Status**: [status.railway.app](https://status.railway.app)
- **Documentation**: [docs.railway.app](https://docs.railway.app)

---

Your PawMatch backend is now deployed on Railway! 🎉
