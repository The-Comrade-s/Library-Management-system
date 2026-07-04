"""
config.py - Application Configuration
======================================
Central configuration file for all environments.
Reads from environment variables with sensible defaults.
Save at: LMS/config.py
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    # ─── Security ───────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-prod-abc123xyz'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # ─── Database ────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///library.db'  # SQLite fallback for local dev without Postgres
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # Fix Render PostgreSQL URL format (postgres:// → postgresql://)
    @staticmethod
    def fix_db_url(url):
        if url and url.startswith('postgres://'):
            return url.replace('postgres://', 'postgresql://', 1)
        return url

    # ─── Session ─────────────────────────────────────────────────────────────
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False   # Set True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ─── File Uploads ────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'app/static/images/covers')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    # ─── Mail ────────────────────────────────────────────────────────────────
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@library.com')

    # ─── Library Business Rules ───────────────────────────────────────────────
    DAILY_FINE_RATE = float(os.environ.get('DAILY_FINE_RATE', 0.50))   # $ per day
    BORROW_DURATION_DAYS = int(os.environ.get('BORROW_DURATION_DAYS', 14))  # days
    MAX_BOOKS_PER_USER = 5  # Maximum books a member can borrow at once

    # ─── Pagination ──────────────────────────────────────────────────────────
    BOOKS_PER_PAGE = 12
    USERS_PER_PAGE = 20
    BORROWS_PER_PAGE = 20
    REPORTS_PER_PAGE = 25

    # ─── Admin Seed ──────────────────────────────────────────────────────────
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@library.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Admin@123456')
    ADMIN_FIRST_NAME = os.environ.get('ADMIN_FIRST_NAME', 'System')
    ADMIN_LAST_NAME = os.environ.get('ADMIN_LAST_NAME', 'Administrator')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = Config.fix_db_url(
        os.environ.get('DATABASE_URL') or 'sqlite:///library_dev.db'
    )


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class ProductionConfig(Config):
    """Production configuration (Render deployment)."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    SQLALCHEMY_DATABASE_URI = Config.fix_db_url(
        os.environ.get('DATABASE_URL')
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20,
    }


# ─── Configuration Mapping ───────────────────────────────────────────────────
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
