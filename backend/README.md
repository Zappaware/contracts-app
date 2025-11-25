# Contract Management API

## How to Run the Project

### Using Docker (Recommended)

1. **Clone the repository and navigate to the directory:**
   ```bash
   cd contracts/backend
   ```

2. **Copy the configuration file:**
   ```bash
   cp .env.example .env
   ```

3. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   
   **Note for Mac M1:** The SQL Server container uses `platform: linux/amd64` for compatibility.

4. **Create the database (first time):**
   ```bash
   # Connect to SQL Server container
   docker exec -it contract_management_db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'YourPassword123!'
   
   # Create the database
   CREATE DATABASE contract_management;
   GO
   exit
   ```

5. **Run migrations:**
   ```bash
   # From the API container or locally
   docker exec -it contract_management_api alembic upgrade head
   ```

6. **The API will be available at:**
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/api/v1/health

7. **To run with SQLPad (optional):**
   ```bash
   docker-compose --profile tools up --build
   ```
   - SQLPad: http://localhost:3000 (admin@contract.com / admin123)

### Local Development

1. **Install SQL Server ODBC Driver 18 for macOS:**
   ```bash
   # Install Homebrew if you don't have it
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Install ODBC driver
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew update
   brew install msodbcsql18 mssql-tools18
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure SQL Server database and update .env**

5. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

6. **Run the application:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Useful Commands

- **Stop containers:** `docker-compose down`
- **View logs:** `docker-compose logs -f api`
- **View SQL Server logs:** `docker-compose logs -f db`
- **Create migration:** `alembic revision --autogenerate -m "description"`
- **Apply migrations:** `alembic upgrade head`
- **Connect to SQL Server:** `docker exec -it contract_management_db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'YourPassword123!'`

### SQL Server Configuration

- **User:** sa
- **Password:** YourPassword123!
- **Port:** 1433
- **Database:** contract_management

### Important Notes

- SQL Server requires complex passwords (minimum 8 characters, uppercase, lowercase, numbers and symbols)
- On Mac M1, SQL Server runs in x86_64 emulation mode
- ODBC Driver 18 requires `TrustServerCertificate=yes` for local connections

---

## Roles and Permissions

### Available Roles

The system has three main roles for managing contracts and vendors:

#### 1. Contract Admin (Contract Administrator)
**Description:** Role with full permissions to manage vendors and contracts.

**Permissions:**
- ✅ **Create** new vendors
- ✅ **Create** new contracts
- ✅ **Edit** existing vendor information
- ✅ **Edit** existing contract information
- ✅ **Delete** vendors
- ✅ **Delete** contracts
- ✅ **View** all vendors and contracts
- ✅ **Upload/Update/Delete** documents
- ✅ **Access** admin dashboard
- ✅ **View** pending documents workbasket
- ✅ **Take actions** on any contract

**Accessible Endpoints:**
- `POST /vendors/` - Create vendor
- `PUT /vendors/{id}` - Edit vendor
- `DELETE /vendors/{id}` - Delete vendor
- `POST /contracts/` - Create contract
- `PUT /contracts/{id}` - Edit contract
- `DELETE /contracts/{id}` - Delete contract
- `GET /dashboards/admin` - Admin dashboard
- `GET /dashboards/pending-documents` - Pending documents
- All read endpoints

---

#### 2. Contract Manager
**Description:** Role for users who manage specific contracts assigned to them.

**Permissions:**
- ✅ **View** all vendors
- ✅ **View** all contracts
- ✅ **View** complete contract details
- ✅ **Search and filter** vendors and contracts
- ✅ **Access** their personal dashboard
- ✅ **View** expiring contracts (where they are owner)
- ✅ **Take actions** on own contracts:
  - Extend expiration date
  - Mark for termination
  - Upload termination documents
- ❌ **CANNOT** create vendors or contracts
- ❌ **CANNOT** edit vendor information
- ❌ **CANNOT** edit other users' contracts
- ❌ **CANNOT** delete vendors or contracts

**Accessible Endpoints:**
- `GET /vendors/` - List vendors
- `GET /vendors/{id}` - View vendor
- `GET /contracts/` - List contracts
- `GET /contracts/{id}` - View contract
- `GET /dashboards/manager` - Personal dashboard
- `POST /contracts/{id}/extend` - Extend own contract
- `POST /contracts/{id}/save-pending-termination` - Save termination decision
- `POST /contracts/{id}/terminate` - Terminate own contract
- `GET /dashboards/owner/expiring-contracts` - View expiring contracts
- `GET /dashboards/owner/pending-terminations` - View pending terminations

---

#### 3. Contract Manager Backup
**Description:** Role for users designated as backup for Contract Managers.

**Permissions:**
- ✅ **View** all vendors
- ✅ **View** all contracts
- ✅ **View** complete contract details
- ✅ **Search and filter** vendors and contracts
- ✅ **Access** dashboard for contracts where they are backup
- ✅ **View** expiring contracts (where they are backup)
- ✅ **View** contracts with pending documents (where they are backup)
- ❌ **CANNOT** create vendors or contracts
- ❌ **CANNOT** edit information
- ❌ **CANNOT** delete vendors or contracts
- ❌ **CANNOT** take actions on contracts (view only)

**Accessible Endpoints:**
- `GET /vendors/` - List vendors
- `GET /vendors/{id}` - View vendor
- `GET /contracts/` - List contracts
- `GET /contracts/{id}` - View contract
- `GET /dashboards/backup/expiring-contracts` - View expiring contracts
- `GET /dashboards/backup/pending-terminations` - View pending terminations

---

### Security Implementation

#### Authentication
The system uses **JWT (JSON Web Tokens)** for authentication:

```python
from app.core.security import get_current_active_user

@router.get("/protected-endpoint")
def protected_route(current_user: User = Depends(get_current_active_user)):
    # Only authenticated users can access
    return {"user": current_user.email}
```

#### Role-Based Authorization

To restrict endpoints by role:

```python
from app.core.security import require_contract_admin, require_contract_manager

# Contract Admin only
@router.post("/vendors/")
def create_vendor(current_user: User = Depends(require_contract_admin)):
    # Only Contract Admin can create vendors
    pass

# Contract Manager or higher
@router.get("/dashboards/manager")
def get_manager_dashboard(current_user: User = Depends(require_contract_manager)):
    # Contract Manager and Contract Admin can access
    pass
```

#### Ownership Verification

For actions on specific contracts:

```python
# Verify user is owner or admin
is_owner = contract.contract_owner_id == current_user.id
is_admin = current_user.role == UserRole.CONTRACT_ADMIN

if not (is_owner or is_admin):
    raise HTTPException(status_code=403, detail="You don't have permission")
```

---

### Permissions Matrix

| Action | Contract Admin | Contract Manager | Contract Manager Backup |
|--------|---------------|------------------|------------------------|
| Create Vendor | ✅ | ❌ | ❌ |
| Edit Vendor | ✅ | ❌ | ❌ |
| Delete Vendor | ✅ | ❌ | ❌ |
| View Vendors | ✅ | ✅ | ✅ |
| Create Contract | ✅ | ❌ | ❌ |
| Edit Contract | ✅ | ✅ (own only) | ❌ |
| Delete Contract | ✅ | ❌ | ❌ |
| View Contracts | ✅ | ✅ | ✅ |
| Extend Contract | ✅ | ✅ (own only) | ❌ |
| Terminate Contract | ✅ | ✅ (own only) | ❌ |
| Upload Documents | ✅ | ✅ (own only) | ❌ |
| Admin Dashboard | ✅ | ❌ | ❌ |
| Manager Dashboard | ✅ | ✅ | ❌ |
| Backup Dashboard | ✅ | ❌ | ✅ |

---

### Role Assignment

Roles are assigned at the user level in the database:

```sql
-- Assign Contract Admin role
UPDATE users SET role = 'Contract Admin' WHERE email = 'admin@example.com';

-- Assign Contract Manager role
UPDATE users SET role = 'Contract Manager' WHERE email = 'manager@example.com';

-- Assign Contract Manager Backup role
UPDATE users SET role = 'Contract Manager Backup' WHERE email = 'backup@example.com';
```

Or through the user creation endpoint:

```python
POST /contracts/users/
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "department": "IT",
    "position": "Contract Manager",
    "role": "Contract Manager"
}
```

---

### Important Notes about Roles

1. **Contract Owner vs Contract Manager:**
   - In the data model, `contract_owner_id` refers to the **Contract Manager** responsible for the contract
   - `contract_owner_manager_id` refers to the **Contract Owner** (supervisor)
   - `contract_owner_backup_id` refers to the **Contract Manager Backup**

2. **Role Hierarchy:**
   - Contract Admin > Contract Manager > Contract Manager Backup
   - Contract Admin can perform all actions
   - Contract Manager can manage their assigned contracts
   - Contract Manager Backup can only view

3. **Security:**
   - All endpoints require JWT authentication
   - Roles are verified on each request
   - Actions are logged in audit trail (last_modified_by, last_modified_date)

---