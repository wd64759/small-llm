from dotenv import load_dotenv
import os
from typing import Optional

# Load environment variables from .env file
load_dotenv()

class EnvConfig:
    """Environment configuration manager"""
    
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable with optional default value"""
        return os.getenv(key, default)
    
    @staticmethod
    def get_required(key: str) -> str:
        """Get required environment variable, raises error if not found"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' not found")
        return value
    
    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Get integer environment variable"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

# Common environment variables
class Config:
    """Common configuration constants"""
    OPENAI_API_KEY = EnvConfig.get('OPENAI_API_KEY', '')  # Will be validated when used
    OPENAI_BASE_URL = EnvConfig.get('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL = EnvConfig.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # Vector database configuration
    VECTOR_DB_PATH = EnvConfig.get('VECTOR_DB_PATH', './data/knowledge_base')
    
    # Logging configuration
    LOG_LEVEL = EnvConfig.get('LOG_LEVEL', 'INFO')
    
    # API configuration
    API_HOST = EnvConfig.get('API_HOST', '0.0.0.0')
    API_PORT = EnvConfig.get_int('API_PORT', 8000) 