# Database Setup Notes

## Quick Reference

### Default Users (Auto-seeded)

| Email | Password | Role | Department |
|-------|----------|------|------------|
| william.defoe@arubabank.com | password123 | Contract Admin | IT |
| john.doe@arubabank.com | password123 | Contract Manager | Operations |
| jane.smith@arubabank.com | password123 | Contract Manager Backup | Finance |

### Local Development Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run migrations
alembic upgrade head

# 3. Seed users (first time only)
python seed_users.py

# 4. Start application
uvicorn main:root_app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

```bash
# Starts everything automatically (migrations + user seeding)
docker-compose up --build

# Access at http://localhost:8000
```

### Manual User Creation via API

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@arubabank.com",
    "password": "securepassword",
    "first_name": "John",
    "last_name": "Doe",
    "department": "IT",
    "position": "Developer",
    "role": "Contract Manager"
  }'
```

### Database Commands

```bash
# Connect to PostgreSQL
psql postgresql://postgres:postgres123@localhost:5432/aruba_bank_db

# List users
SELECT id, user_id, first_name, last_name, email, role, is_active FROM users;

# List vendors
SELECT id, vendor_id, vendor_name, status FROM vendors;

# List contracts
SELECT id, contract_id, contract_type, start_date, end_date FROM contracts;
```

## Files Modified

1. **seed_users.py** - New script to seed initial users
2. **docker-entrypoint.sh** - New entrypoint script for Docker (runs migrations + seeds)
3. **Dockerfile** - Updated to use entrypoint script
4. **README.md** - Added documentation for database initialization
5. **.env** - Updated DATABASE_URL with proper credentials

## Important Notes

- The seed script is **idempotent** - safe to run multiple times
- Docker container **automatically** runs migrations and seeding on startup
- Default passwords should be **changed in production**
- User IDs are auto-generated (U1, U2, U3, etc.)

