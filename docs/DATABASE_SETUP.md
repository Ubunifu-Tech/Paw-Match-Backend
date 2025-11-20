# PostgreSQL Database Setup Guide

## Step 1: Create the Database

```bash
# Connect to PostgreSQL as superuser
psql postgres

# Create database
CREATE DATABASE dogmatch;

# Create user (if needed)
CREATE USER dogmatch_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dogmatch TO dogmatch_user;

# Exit psql
\q
```

## Step 2: Update .env File

Update your `.env` file with the correct database credentials:

```bash
# If using default postgres user
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/dogmatch

# OR if you created a custom user
DATABASE_URL=postgresql+asyncpg://dogmatch_user:your_secure_password@localhost:5432/dogmatch
```

## Step 3: Initialize Database Schema

The database tables will be created automatically when you first start the application. SQLAlchemy will create all tables defined in your models.

```bash
# Simply start the application and tables will be created
uvicorn app.main:app --reload
```

Alternatively, you can create tables manually using a Python script if needed.

## Step 4: Verify Database

```bash
# Connect to database
psql -d dogmatch

# List tables
\dt

# You should see:
# - sessions
# - chat_messages
# - saved_results
# - users
# - breeds
# - favorites

# Check table structure
\d sessions
\d chat_messages
\d saved_results

# Exit
\q
```

## Common Issues

### Issue 1: Password Authentication Failed

**Solution**: Update the password in your `.env` file to match your PostgreSQL password.

```bash
# Find your PostgreSQL password or reset it
psql postgres
ALTER USER postgres WITH PASSWORD 'new_password';
```

### Issue 2: Database Does Not Exist

**Solution**: Create the database first:

```bash
psql postgres
CREATE DATABASE dogmatch;
```

### Issue 3: Connection Refused

**Solution**: Ensure PostgreSQL is running:

```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL (macOS with Homebrew)
brew services start postgresql@14

# OR (if installed via Postgres.app)
# Open Postgres.app
```

## Next Steps

Once the database is set up:

1. ✅ Database tables created
2. ✅ Database connection configured
3. ⏭️ Load initial breed data using scripts
4. ⏭️ Test API endpoints
5. ⏭️ Set up data backup procedures

## Database Schema

### sessions
- `id` (UUID, PK)
- `session_data` (JSONB)
- `user_profile` (JSONB)
- `is_complete` (BOOLEAN)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)
- `expires_at` (TIMESTAMP)

### chat_messages
- `id` (BIGINT, PK)
- `session_id` (UUID, FK → sessions.id)
- `role` (VARCHAR)
- `content` (TEXT)
- `message_metadata` (JSONB)
- `created_at` (TIMESTAMP)

### saved_results
- `id` (UUID, PK)
- `session_id` (UUID)
- `breed_name` (VARCHAR)
- `match_score` (NUMERIC)
- `rank` (INTEGER)
- `match_data` (JSONB)
- `video_url` (TEXT)
- `images_used` (JSONB)
- `created_at` (TIMESTAMP)

## Useful Commands

```bash
# Connect to database
psql -d dogmatch

# List all tables
\dt

# Describe table structure
\d table_name

# View table data
SELECT * FROM table_name LIMIT 10;

# Export schema
pg_dump -s dogmatch > schema.sql

# Backup database
pg_dump dogmatch > backup.sql
```
