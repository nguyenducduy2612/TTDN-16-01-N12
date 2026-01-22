"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"
    
    # Odoo
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_password: str
    
    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug: bool = False
    
    # CORS
    cors_origins: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()
