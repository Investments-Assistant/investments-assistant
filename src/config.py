"""Configuration for the investment agent."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    
    # Agent Configuration
    AGENT_TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", 0.7))
    AGENT_MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", 2048))
    
    # Streamlit Configuration
    STREAMLIT_SERVER_PORT = int(os.getenv("STREAMLIT_SERVER_PORT", 8501))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


def get_config():
    """Get configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        return ProductionConfig()
    
    return DevelopmentConfig()


config = get_config()
