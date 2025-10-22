from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # Project Info
    project_name: str = "Resume Intelligence AI"
    version: str = "1.0.0"
    debug: bool = True
    
    # Neo4j Configuration
    neo4j_uri: str = Field(default="neo4j://127.0.0.1:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="laavanya", env="NEO4J_PASSWORD")
    neo4j_database: str = Field(default="neo4j", env="NEO4J_DATABASE")
    
    # FastAPI Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True
    
    # File Upload Configuration
    upload_dir: Path = Path("data/uploads")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf", ".docx", ".doc"]
    
    # Reddit API Configuration (for later)
    reddit_client_id: Optional[str] = Field(default=None, env="REDDIT_CLIENT_ID")
    reddit_client_secret: Optional[str] = Field(default=None, env="REDDIT_CLIENT_SECRET")
    reddit_user_agent: str = "ResumeIntelligenceBot/1.0"
    
    # Gemini AI Configuration
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    
    # NLP Configuration
    spacy_model: str = "en_core_web_sm"
    max_text_length: int = 1000000  # 1MB of text
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    model_config = {
    "env_file": ".env",
    "case_sensitive": False,
    "extra": "ignore"  # This will ignore extra env vars
}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

# Validate critical settings on startup
def validate_settings():
    """Validate critical configuration on startup"""
    if not settings.neo4j_uri:
        raise ValueError("Neo4j URI must be configured")
    
    if not settings.neo4j_password or settings.neo4j_password == "password123":
        print("⚠️  Warning: Using default Neo4j password. Change for production!")
    
    print(f"✅ Configuration loaded:")
    print(f"   - Neo4j: {settings.neo4j_uri}")
    print(f"   - Upload dir: {settings.upload_dir}")
    print(f"   - Max file size: {settings.max_file_size / 1024 / 1024}MB")
    print(f"   - Gemini API: {'Configured' if settings.gemini_api_key else 'Not configured'}")

if __name__ == "__main__":
    validate_settings()