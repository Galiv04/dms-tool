from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    # App Information (centralizzate dai main.py)
    app_name: str = Field(default="Document Management System")
    app_description: str = Field(default="Sistema di gestione documenti con approvazioni workflow")
    app_version: str = Field(default="1.0.0")
    app_features: list = Field(default=[
        "User authentication",
        "Document management", 
        "Approval workflow",
        "Audit logging"
    ])
    
    model_config = ConfigDict(env_file=".env")
    
    # Database
    database_url: str = Field(default="sqlite:///./data/app.db")
    
    # JWT Security
    secret_key: str = Field(default="your-secret-key-change-this-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    
    # CORS Settings
    cors_origins: list = Field(default=["http://localhost:5173", "http://localhost:3000"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list = Field(default=["*"])
    cors_allow_headers: list = Field(default=["*"])
    
    # Storage settings
    storage_path: str = Field(default="./storage")
    static_files_path: str = Field(default="./static")
    max_file_size: int = Field(default=50 * 1024 * 1024)  # 50MB
    allowed_file_types: list = Field(default=[
        "pdf", "doc", "docx", "txt", "rtf",
        "jpg", "jpeg", "png", "gif", "bmp",
        "xls", "xlsx", "ppt", "pptx"
    ])
    
    # Email Settings (per approvazioni)
    email_enabled: bool = Field(default=False)
    smtp_server: str = Field(default="localhost")
    smtp_port: int = Field(default=587)
    smtp_username: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_use_tls: bool = Field(default=True)
    email_from: str = Field(default="noreply@dms.local")
    
    # Approval Workflow Settings
    approval_token_expire_days: int = Field(default=7)
    approval_reminder_days: int = Field(default=3)
    max_recipients_per_request: int = Field(default=20)
    approval_url_base: str = Field(default="http://localhost:5173/approval")
    
    # Security Settings
    password_min_length: int = Field(default=8)
    password_require_uppercase: bool = Field(default=True)
    password_require_lowercase: bool = Field(default=True)
    password_require_numbers: bool = Field(default=True)
    password_require_special: bool = Field(default=True)
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100)
    rate_limit_period: int = Field(default=3600)  # 1 hour
    
    # Logging
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="./logs/app.log")
    
    # Development/Debug
    debug: bool = Field(default=False)
    reload: bool = Field(default=False)

settings = Settings()
