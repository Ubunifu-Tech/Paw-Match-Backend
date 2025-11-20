# Database Management (Without Migrations)

This project has been configured to manage database schema directly without migration tools like Alembic.

## How Database Schema is Managed

### Automatic Table Creation

When the application starts, SQLAlchemy will automatically create any missing tables based on the model definitions in:
- `app/db/models/` - Core models (Session, ChatMessage, SavedResult)
- `app/models/` - Feature models (User, Breed, Favorite, etc.)

**No manual migration steps needed for initial setup!**

## Initial Setup

### 1. Configure Database Connection

Set your `DATABASE_URL` in `.env`:

```bash
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/dogmatch

# Railway/Production (auto-configured)
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### 2. Initialize Database (Optional)

You can use the initialization script to explicitly create all tables:

```bash
python scripts/init_database.py
```

This will:
- ✅ Test the database connection
- ✅ Create all tables from models
- ✅ Show you what was created

**Or** just start the app - tables will be created automatically on first run!

## Making Schema Changes

### When You Add/Modify Models:

1. **Edit your model files** in `app/models/` or `app/db/models/`
2. **Drop and recreate tables** (development only):
   ```bash
   python scripts/init_database.py --drop
   python scripts/init_database.py
   ```

3. **Or use SQL for targeted changes** (production):
   ```bash
   psql -d dogmatch
   ALTER TABLE users ADD COLUMN new_field VARCHAR(255);
   ```

### Production Schema Changes

For production databases:

1. **Create a SQL script** with your changes
2. **Test in staging** environment first
3. **Backup your database** before applying
4. **Apply manually** via psql or Railway CLI

```bash
# Example: Add a column
psql $DATABASE_URL -c "ALTER TABLE users ADD COLUMN phone VARCHAR(20);"

# Or via Railway CLI
railway run psql -c "ALTER TABLE users ADD COLUMN phone VARCHAR(20);"
```

## Loading Initial Data

Use scripts to populate initial data (like breeds):

```bash
# Load breed data
python populate_breeds.py

# Seed database for testing
python scripts/seed_breeds.py
```

## Database Utilities

### View Current Schema

```bash
# Connect to database
psql $DATABASE_URL

# List all tables
\dt

# Describe a table
\d users

# View data
SELECT * FROM users LIMIT 10;
```

### Backup & Restore

```bash
# Create backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20241120.sql

# Export schema only
pg_dump -s $DATABASE_URL > schema.sql
```

### Reset Database (Development Only)

```bash
# Drop all tables and recreate
python scripts/init_database.py --drop
python scripts/init_database.py

# Reload data
python populate_breeds.py
```

## Railway Deployment

When deploying to Railway:

1. **Database tables are created automatically** on first startup
2. **No migration commands needed** in your deploy configuration
3. **Load data separately** using scripts after deployment:
   ```bash
   railway run python populate_breeds.py
   ```

## Benefits of This Approach

✅ **Simpler** - No migration file management  
✅ **Faster** - No migration overhead on deployment  
✅ **Flexible** - Easy to reset in development  
✅ **Direct** - Use SQL when you need precision  
✅ **Suitable for smaller projects** - Less complexity for manageable databases  

## When to Consider Migrations

Consider adding a migration tool (like Alembic) back if:
- Your database is large and complex
- You have production data that requires careful schema evolution
- Multiple developers are making concurrent schema changes
- You need to track schema history precisely
- You need rollback capabilities

For now, this simpler approach works well for this project's scale!

## Troubleshooting

### Tables Not Created

**Issue**: Tables aren't being created automatically

**Solution**:
1. Check your DATABASE_URL is correct
2. Ensure models are imported in `app/core/database.py`
3. Run the init script manually: `python scripts/init_database.py`

### Schema Out of Sync

**Issue**: Model changes not reflected in database

**Solution**:
1. Development: Drop and recreate tables
2. Production: Apply SQL changes manually
3. Always backup before making changes!

### Connection Issues

**Issue**: Can't connect to database

**Solution**:
1. Verify PostgreSQL is running: `pg_isready`
2. Check DATABASE_URL format: `postgresql+asyncpg://...`
3. Test connection: `psql $DATABASE_URL`

## Questions?

See also:
- `docs/DATABASE_SETUP.md` - Complete database setup guide
- `docs/RAILWAY_DEPLOYMENT.md` - Deployment instructions
- `scripts/init_database.py` - Database initialization script
