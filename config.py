import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'unisync-french-cafe-secret-key-2026-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        f'sqlite:///{os.path.join(BASE_DIR, "instance", "database.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 45-second QR feedback session duration
    QR_FEEDBACK_DURATION_SECONDS = 45
    
    # Faculty verification passkey for security
    FACULTY_VERIFICATION_KEY = os.environ.get('FACULTY_VERIFICATION_KEY', 'FACULTY2026')
    
    # Session cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # Set to True in HTTPS production

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    QR_FEEDBACK_DURATION_SECONDS = 45
