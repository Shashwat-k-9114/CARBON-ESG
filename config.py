import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-dev-key-do-not-use-in-prod'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'database/carbon_esg.db')
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/reports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
