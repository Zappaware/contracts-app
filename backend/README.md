# Contract Management API

## Cómo correr el proyecto

### Usando Docker (Recomendado)

1. **Clonar el repositorio y navegar al directorio:**
   ```bash
   cd aruba-bank-backend
   ```

2. **Copiar el archivo de configuración:**
   ```bash
   cp .env.example .env
   ```

3. **Construir y ejecutar con Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   
   **Nota para Mac M1:** El contenedor de SQL Server usa `platform: linux/amd64` para compatibilidad.

4. **Crear la base de datos (primera vez):**
   ```bash
   # Conectarse al contenedor de SQL Server
   docker exec -it contract_management_db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'YourPassword123!'
   
   # Crear la base de datos
   CREATE DATABASE contract_management;
   GO
   exit
   ```

5. **Ejecutar migraciones:**
   ```bash
   # Desde el contenedor de la API o localmente
   docker exec -it contract_management_api alembic upgrade head
   ```

6. **La API estará disponible en:**
   - API: http://localhost:8000
   - Documentación: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/api/v1/health

7. **Para ejecutar con SQLPad (opcional):**
   ```bash
   docker-compose --profile tools up --build
   ```
   - SQLPad: http://localhost:3000 (admin@contract.com / admin123)

### Desarrollo Local

1. **Instalar SQL Server ODBC Driver 18 para macOS:**
   ```bash
   # Instalar Homebrew si no lo tienes
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   
   # Instalar el driver ODBC
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew update
   brew install msodbcsql18 mssql-tools18
   ```

2. **Crear entorno virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar base de datos SQL Server y actualizar .env**

5. **Ejecutar migraciones:**
   ```bash
   alembic upgrade head
   ```

6. **Ejecutar la aplicación:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Comandos útiles

- **Parar los contenedores:** `docker-compose down`
- **Ver logs:** `docker-compose logs -f api`
- **Ver logs de SQL Server:** `docker-compose logs -f db`
- **Crear migración:** `alembic revision --autogenerate -m "descripción"`
- **Aplicar migraciones:** `alembic upgrade head`
- **Conectar a SQL Server:** `docker exec -it contract_management_db /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'YourPassword123!'`

### Configuración de SQL Server

- **Usuario:** sa
- **Contraseña:** YourPassword123!
- **Puerto:** 1433
- **Base de datos:** contract_management

### Notas importantes

- SQL Server requiere contraseñas complejas (mínimo 8 caracteres, mayúsculas, minúsculas, números y símbolos)
- En Mac M1, SQL Server se ejecuta en modo de emulación x86_64
- El driver ODBC 18 requiere `TrustServerCertificate=yes` para conexiones locales