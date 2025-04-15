import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ndiha_sha.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', 'your-api-key')
    
    # Session security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Template configuration
    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False  # Disable debug mode for production
    TEMPLATE_FOLDER = 'templates'  # Explicitly set template folder
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')
    
    # Form configuration
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    WTF_CSRF_HEADERS = ['X-CSRFToken', 'X-CSRF-Token']
    WTF_CSRF_FIELD_NAME = 'csrf_token'