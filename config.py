import os

class Config:
    SECRET_KEY = 'your-secret-key-change-this-in-production'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/carbon_esg.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/reports'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size