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

## Step 3: Run Migrations

```bash
# Activate virtual environment
cd backend
source venv/bin/activate

# Create initial migration
alembic revision --autogenerate -m "Initial migration: sessions and saved results"

# Apply migration
alembic upgrade head
```

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
# - alembic_version

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
2. ✅ Migrations configured
3. ⏭️ Update ConversationAgent to use database instead of in-memory storage
4. ⏭️ Implement session persistence
5. ⏭️ Add saved results functionality

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
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current migration version
alembic current

# Show migration history
alembic history
```
