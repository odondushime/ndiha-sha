import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')  # Secure key for sessions
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ndiha_sha.db'      # SQLite database path
    SQLALCHEMY_TRACK_MODIFICATIONS = False                  # Disable modification tracking
    EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY', 'your-api-key')  # API key for currency conversion