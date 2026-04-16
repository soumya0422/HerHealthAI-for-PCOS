import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'herhealthai-super-secret-key-2026-pcos')
    ALGORITHM: str = 'HS256'
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    FRONTEND_ORIGINS: str = os.getenv('FRONTEND_ORIGINS', '*')
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///./herhealthai.db')

settings = Settings()
