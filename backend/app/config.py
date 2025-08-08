from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")  # ← Fix Pydantic V2
    
    app_name: str = "DMS Tool"
    database_url: str = Field(default="sqlite:///./data/app.db")
    secret_key: str = Field(default="ciao")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
