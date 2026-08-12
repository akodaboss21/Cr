# Supabase Migration & Deployment Guide

## 1. Apply Migrations to Supabase

### Prerequisites
- Supabase project created
- Database credentials available
- Alembic installed in virtual environment

### Steps

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Install dependencies
pip install alembic psycopg2-binary supabase

# 3. Initialize Alembic (if not already done)
alembic init alembic

# 4. Configure alembic.ini with Supabase DATABASE_URL
# Edit alembic.ini:
# sqlalchemy.url = postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# 5. Generate initial migration
alembic revision --autogenerate -m "Initial schema"

# 6. Apply migrations to Supabase
alembic upgrade head
```

## 2. Test Authentication Flows

### User Registration
```bash
curl -X POST http://localhost:8000/api/v1/users/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "first_name": "Test",
    "last_name": "User",
    "is_active": true
  }'
```

### User Login (via Supabase)
```bash
curl -X POST "https://YOUR_PROJECT.supabase.co/auth/v1/token?grant_type=password" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

### Token Refresh
```bash
curl -X POST "https://YOUR_PROJECT.supabase.co/auth/v1/token?grant_type=refresh_token" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

### Admin Operations
```bash
# List users (requires admin token)
curl -X GET http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Update user
curl -X PUT http://localhost:8000/api/v1/users/USER_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "Name"
  }'

# Delete user
curl -X DELETE http://localhost:8000/api/v1/users/USER_ID \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 3. Deploy to Production

### Environment Variables
Update `.env.local` with real Supabase credentials:
```bash
SUPABASE_PROJECT_ID=your-actual-project-id
SUPABASE_DB_PASSWORD=your-actual-db-password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-actual-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-actual-service-role-key
```

### Docker Deployment
```bash
# Build and start services
docker-compose up -d --build

# Check logs
docker-compose logs -f backend

# Verify health
curl http://localhost:8000/health
```

### Production Checklist
- [ ] Supabase project created and configured
- [ ] Database migrations applied successfully
- [ ] Authentication flows tested and working
- [ ] Environment variables set with real credentials
- [ ] Docker services running and healthy
- [ ] SSL certificates configured (for production)
- [ ] Domain configured and pointing to server
- [ ] Monitoring and logging set up
- [ ] Backup strategy implemented