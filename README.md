# Aruba Bank Contract Management System

A **monolithic** web application for managing contracts and vendors, built with FastAPI (backend) and NiceGUI (frontend) running as a **single container deployment**.

## Features

- **Contract Management**: Create, edit, view, and manage contracts (active, pending, expired, terminated)
- **Vendor Management**: Add and manage vendor information
- **User Authentication**: JWT-based authentication with role-based access control
- **Dashboard Views**: Different dashboards for Contract Admin, Contract Manager, and Backup roles
- **Document Management**: Upload and manage contract documents
- **API & Web UI**: RESTful API endpoints + interactive web interface in a single application
- **New Relic Monitoring**: Integrated APM monitoring with timestamped logs

## Architecture

This is a **monolithic application** that runs:
- FastAPI REST API
- NiceGUI Web UI
- Business logic and services

All in a **single container**, making deployment simple and straightforward.

## Technology Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Alembic
- **Frontend**: NiceGUI (Python-based web UI framework)
- **Authentication**: JWT tokens with role-based permissions
- **Monitoring**: New Relic APM
- **Containerization**: Docker (single container deployment)

## Quick Start with Docker (Recommended)

### 1. Navigate to the project directory

```bash
cd contracts
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` to customize:
- Database credentials
- Secret keys
- New Relic license key (if using)

### 3. Start the monolithic application

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL database** (port 5433)
- **Monolithic app container** with FastAPI + NiceGUI (port 8000)

### 4. Access the application

Once running:
- **Web UI**: http://localhost:8000/
- **Login Page**: http://localhost:8000/login
- **API Documentation**: http://localhost:8000/api/v1/docs
- **API Health Check**: http://localhost:8000/api/v1/health

**Default Users** (automatically seeded on first run):

| Email | Password | Role | Department |
|-------|----------|------|------------|
| william.defoe@arubabank.com | password123 | Contract Admin | IT |
| john.doe@arubabank.com | password123 | Contract Manager | Operations |
| jane.smith@arubabank.com | password123 | Contract Manager Backup | Finance |

> ⚠️ **Important**: Change these passwords in production!

### 5. Stop the application

```bash
docker-compose down
```

To also remove volumes (database data):

```bash
docker-compose down -v
```

## Local Development (Without Docker)

### Prerequisites

- Python 3.11+
- PostgreSQL database

### Setup

1. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure database**

Update `.env` with your PostgreSQL connection string:

```
DATABASE_URL=postgresql://user:password@localhost:5432/aruba_bank
```

4. **Run migrations**

```bash
alembic upgrade head
```

5. **Seed initial users** (first time only)

```bash
python seed_users.py
```

This creates 3 default users (see table above). The script is safe to run multiple times - it will skip if users already exist.

6. **Start the monolithic application**

```bash
uvicorn main:root_app --reload --host 0.0.0.0 --port 8000
```

7. **Access the application**

- Web UI: http://localhost:8000/
- API Docs: http://localhost:8000/api/v1/docs

## Production Deployment

### Single Container Deployment

The application is designed as a **monolithic single-container** application for simple deployment:

1. **Build the Docker image**:

```bash
docker build -t aruba-bank-contracts:latest .
```

2. **Run the container**:

```bash
docker run -d \
  --name aruba-bank-app \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql://user:pass@db-host:5432/aruba_bank" \
  -e SECRET_KEY="your-production-secret-key" \
  -e NEW_RELIC_LICENSE_KEY="your-newrelic-key" \
  -e NEW_RELIC_APP_NAME="Aruba Bank Contracts" \
  aruba-bank-contracts:latest
```

3. **Using with Aruba Bank's Container Registry**:

```bash
# Tag for registry
docker tag aruba-bank-contracts:latest registry.arubabank.com/contracts:latest

# Push to registry
docker push registry.arubabank.com/contracts:latest

# Deploy from registry
docker run -d registry.arubabank.com/contracts:latest
```

### Key Benefits of Monolithic Architecture

- **Simple Deployment**: Single container to manage
- **Reduced Complexity**: No need to orchestrate multiple services
- **Easy Monitoring**: All logs in one place with timestamps
- **Lower Resource Usage**: Shared memory and processes
- **Fast Development**: Quick iterations and testing

### Kubernetes Deployment (Production)

The application is designed for GitLab CI/CD deployment to Kubernetes:

**Environment Variables** (passed via GitLab CI/CD):
```yaml
DATABASE_URL: postgresql://user:pass@db-host:5432/aruba_bank
SECRET_KEY: <from GitLab secrets>
NEW_RELIC_LICENSE_KEY: <from GitLab secrets>
NEW_RELIC_APP_NAME: "Aruba Bank - Contract Management"
NEW_RELIC_ENVIRONMENT: production
DEBUG: false
```

**Container Configuration**:
- Uses Aruba Bank's base Python image: `registry.arubabank.com/container/python:base-latest`
- Runs on port 8000
- Includes New Relic APM integration
- Timestamped logging via `ts` command

**Health Checks**:
- Liveness probe: `GET /api/v1/health`
- Readiness probe: `GET /api/v1/health`

**Volumes** (if needed):
- `/app/uploads` - For contract documents (use persistent volume or object storage)

## Project Structure

```
contracts/                      # Root - Monolithic application
├── main.py                     # Single entry point (root_app)
├── app/
│   ├── api/                    # FastAPI endpoints
│   ├── components/             # NiceGUI UI components
│   ├── core/                   # Configuration, security
│   ├── db/                     # Database connection
│   ├── models/                 # SQLAlchemy models
│   ├── pages/                  # NiceGUI web pages
│   ├── schemas/                # Pydantic schemas
│   └── services/               # Business logic
├── alembic/                    # Database migrations
├── uploads/                    # Document uploads
├── Dockerfile                  # Aruba Bank standard
├── docker-compose.yml          # Local development
├── requirements.txt            # All dependencies (backend + frontend)
├── .env                        # Environment variables
└── README.md                   # This file
```

## Roles and Permissions

### 1. Contract Admin
- Full permissions to create, edit, delete vendors and contracts
- Access to admin dashboard
- Manage all documents

### 2. Contract Manager
- View all vendors and contracts
- Manage own contracts (extend, terminate)
- Personal dashboard with expiring contracts
- Upload documents for own contracts

### 3. Contract Manager Backup
- View-only access to vendors and contracts
- Dashboard for contracts where they are backup
- Cannot perform actions on contracts

See the detailed permissions matrix in the API documentation.

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/register` - Register new user

### Contracts
- `GET /api/v1/contracts/` - List contracts
- `POST /api/v1/contracts/` - Create contract (Admin only)
- `GET /api/v1/contracts/{id}` - Get contract details
- `PUT /api/v1/contracts/{id}` - Update contract
- `DELETE /api/v1/contracts/{id}` - Delete contract (Admin only)

### Vendors
- `GET /api/v1/vendors/` - List vendors
- `POST /api/v1/vendors/` - Create vendor (Admin only)
- `GET /api/v1/vendors/{id}` - Get vendor details
- `PUT /api/v1/vendors/{id}` - Update vendor (Admin only)

Full API documentation available at `/api/v1/docs` when running.

## Database Migrations

### Create a new migration

```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations

```bash
alembic upgrade head
```

### Rollback migration

```bash
alembic downgrade -1
```

## Database Initialization

### First Time Setup

When setting up a fresh database, you need to:

1. **Run migrations** (creates all tables):
```bash
alembic upgrade head
```

2. **Seed initial users** (creates 3 default users):
```bash
python seed_users.py
```

The seed script creates:
- **Contract Admin** (william.defoe@arubabank.com) - Full permissions
- **Contract Manager** (john.doe@arubabank.com) - Manage contracts
- **Contract Manager Backup** (jane.smith@arubabank.com) - View-only backup role

All default passwords are `password123` - **change these in production!**

### Docker Automatic Initialization

When using Docker (`docker-compose up`), the initialization happens automatically:
- Database migrations run on container startup
- Users are seeded if the database is empty
- No manual intervention needed

### Manual User Creation

To create additional users via API:

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

## Useful Commands

### Docker Commands

```bash
# View logs
docker-compose logs -f app

# Access database
docker exec -it aruba_bank_db psql -U postgres -d aruba_bank

# Rebuild and restart
docker-compose up --build

# Stop and remove containers
docker-compose down -v
```

### Development

```bash
# Run tests
pytest

# Check code formatting
black app/

# Run linter
flake8 app/
```

## Environment Variables

Key environment variables in `.env`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres123@db:5432/aruba_bank

# Application
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
APP_NAME=Contract Management System

# New Relic (for production)
NEW_RELIC_LICENSE_KEY=your-license-key
NEW_RELIC_APP_NAME=Aruba Bank - Contract Management
NEW_RELIC_ENVIRONMENT=production

# CORS (if needed)
ALLOWED_ORIGINS=http://localhost:8000,http://localhost:3000
```

## Security

- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- SQL injection prevention via SQLAlchemy ORM
- CORS middleware for API security

## Troubleshooting

### Port already in use

If port 8000 is occupied:

```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

Or change the port in `docker-compose.yml` or when running locally.

### Database connection issues

Ensure PostgreSQL is running and credentials in `.env` are correct.

```bash
# Check if database is accessible
docker exec -it aruba_bank_db pg_isready -U postgres
```

### Migration errors

If you encounter migration issues:

```bash
# Reset database (WARNING: destroys all data)
docker-compose down -v
docker-compose up --build
```

## License

This project is proprietary software for Aruba Bank.

## Support

For issues or questions, contact the development team.
