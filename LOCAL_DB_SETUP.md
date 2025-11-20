# 🗄️ Local Database Query Guide

## Current Status

Your local database connection needs to be configured. Here's what you need to do:

## Step 1: Check Your PostgreSQL Setup

### Option A: If you have PostgreSQL installed locally

```bash
# Check if PostgreSQL is running
pg_isready

# If not running, start it:
# On macOS with Homebrew:
brew services start postgresql

# On macOS with Postgres.app:
# Just open Postgres.app
```

### Option B: If you DON'T have PostgreSQL installed

You don't need a local database! You can deploy directly to Railway, and it will:
1. Create the database automatically
2. Create all tables on first run
3. You just need to load breed data

**Skip to "Deploy Without Local Database" section below**

## Step 2: Configure Your Local Database Connection

If you DO have PostgreSQL running locally, update your `.env` file:

```bash
# Edit .env file with your actual postgres password
nano .env
```

Update the DATABASE_URL line:
```
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_ACTUAL_PASSWORD@localhost:5432/dogmatch
```

Common default passwords:
- Empty password: `postgresql+asyncpg://postgres@localhost:5432/dogmatch`
- Password "postgres": `postgresql+asyncpg://postgres:postgres@localhost:5432/dogmatch`
- Your custom password: Replace `YOUR_ACTUAL_PASSWORD`

## Step 3: Create the Database

```bash
# Create the database (if it doesn't exist)
createdb dogmatch

# Or with psql:
psql postgres -c "CREATE DATABASE dogmatch;"
```

## Step 4: Initialize Tables and Load Data

```bash
# Create all tables
python3 scripts/init_database.py

# Load breed data
python3 populate_breeds.py

# Query what's in your database
python3 scripts/query_local_db.py
```

---

## Deploy Without Local Database (Recommended)

If you don't have PostgreSQL locally or just want to deploy quickly:

### 1. Ensure your code is ready

```bash
# Make sure all changes are committed
git add .
git commit -m "Remove migrations, clean up database setup"
git push origin main
```

### 2. Deploy to Railway

Railway will automatically:
- ✅ Create PostgreSQL database
- ✅ Set DATABASE_URL environment variable
- ✅ Create all tables on first run

### 3. Load breed data on Railway

```bash
# After deployment, load breeds
railway run python3 populate_breeds.py
```

### 4. Verify

```bash
# Check the data loaded
railway run python3 scripts/query_local_db.py

# Or test the API
curl https://your-app.up.railway.app/api/breeds | jq
```

---

## What Data Needs to be in Production

Based on typical setup, you need:

### ✅ MUST HAVE (Critical for app to work):
1. **Breeds** (~200 dog breeds)
   - Contains: breed names, characteristics, traits
   - Load with: `railway run python3 populate_breeds.py`
   - This is sourced from `app/data/breed_traits.csv`

### 📦 OPTIONAL (Nice to have):
2. **Breed Images** (if you have them)
   - Profile pictures for each breed
   - Better to upload to GCS/S3 and reference URLs
   - Not critical for initial launch

### 🚫 DON'T TRANSFER (Test data):
3. **Users** - Production starts with empty users
4. **Sessions** - Old test sessions aren't needed
5. **Saved Results** - Test results aren't needed
6. **Favorites** - Test favorites aren't needed
7. **Chat Messages** - Old conversations aren't needed

---

## Quick Start (No Local DB)

If you just want to get to production:

```bash
# 1. Commit your code
git add .
git commit -m "Ready for deployment"
git push

# 2. Deploy to Railway (if not already)
# Visit: https://railway.app
# Connect your GitHub repo
# Railway auto-deploys

# 3. Load breed data
railway run python3 populate_breeds.py

# 4. Test
curl https://your-app.up.railway.app/health
curl https://your-app.up.railway.app/api/breeds
```

That's it! 🚀

---

## Troubleshooting

### "Password authentication failed"
- Update DATABASE_URL in `.env` with correct password
- Or remove password: `postgresql+asyncpg://postgres@localhost:5432/dogmatch`

### "Database doesn't exist"
- Run: `createdb dogmatch`

### "No tables found"
- Run: `python3 scripts/init_database.py`

### "No breed data"
- Run: `python3 populate_breeds.py`

### Need Help?
- Check: `DATABASE_MANAGEMENT.md` for full guide
- See: `docs/RAILWAY_DEPLOYMENT.md` for deployment steps
