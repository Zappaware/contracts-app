from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Contract Management API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database settings
    database_url: str = "postgresql://postgres:postgres123@localhost:5432/aruba_bank"
    database_echo: bool = False
    
    # LDAP settings (for future implementation)
    ldap_server: Optional[str] = None
    ldap_base_dn: Optional[str] = None
    ldap_bind_dn: Optional[str] = None
    ldap_bind_password: Optional[str] = None
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API settings
    api_v1_prefix: str = "/api/v1"
    api_base_url: str = Field(
        default="http://127.0.0.1:8000",
        description="Base URL for server-to-server API calls (set API_BASE_URL in Docker)",
    )
    
    # CORS settings
    allowed_origins: list[str] = ["*"]
    allowed_methods: list[str] = ["*"]
    allowed_headers: list[str] = ["*"]
    
    # File upload settings
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads"
    allowed_file_types: list[str] = ["application/pdf"]
    
    # PostgreSQL settings (for Docker)
    postgres_db: str = "aruba_bank"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres123"
    
    # pgAdmin settings
    pgadmin_default_email: str = "admin@arubabank.com"
    pgadmin_default_password: str = "admin123"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields


settings = Settings()