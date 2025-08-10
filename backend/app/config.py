from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
class Settings(BaseSettings):
    app_name: str = "DMS Tool"
    model_config = ConfigDict(env_file=".env")  # ← Fix Pydantic V2
    database_url: str = Field(default="sqlite:///./data/app.db")
    secret_key: str = Field(default="your-secret-key-change-this")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Storage settings
    storage_path: str = Field(default="./storage")
    max_file_size: int = Field(default=50 * 1024 * 1024)  # 50MB
    allowed_file_types: list = Field(default=[
        "pdf", "doc", "docx", "txt", "rtf",
        "jpg", "jpeg", "png", "gif", "bmp",
        "xls", "xlsx", "ppt", "pptx"
    ])
    

settings = Settings()
