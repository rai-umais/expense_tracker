import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kharcha-super-secret-key-change-in-production-2026'
    
    # Handle PostgreSQL URL format if provided (e.g. from cloud providers like Neon / Render)
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = database_url or f"sqlite:///{os.path.join(basedir, 'instance', 'expenses.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
