"""
app/__init__.py - Application Factory
======================================
Creates and configures the Flask application using the Factory Pattern.
This allows multiple instances (testing, production) without conflicts.
Save at: LMS/app/__init__.py
"""

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect

from config import config

# ─── Extension Instances (no app bound yet) ──────────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()
mail = Mail()
csrf = CSRFProtect()


def create_app(config_name=None):
    """
    Application Factory Function.
    Creates and returns a fully configured Flask application instance.
    
    Args:
        config_name: 'development', 'testing', or 'production'
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(__name__)

    # ─── Load Configuration ───────────────────────────────────────────────
    app.config.from_object(config[config_name])

    # ─── Initialise Extensions ────────────────────────────────────────────
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # ─── Login Manager Settings ───────────────────────────────────────────
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    # ─── Register Blueprints ──────────────────────────────────────────────
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

    from app.books import books_bp
    app.register_blueprint(books_bp, url_prefix='/books')

    from app.borrow import borrow_bp
    app.register_blueprint(borrow_bp, url_prefix='/borrow')

    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.reports import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # ─── Main Routes (Index / Home) ───────────────────────────────────────
    from app.main import main_bp
    app.register_blueprint(main_bp)

    # ─── Error Handlers ───────────────────────────────────────────────────
    register_error_handlers(app)

    # ─── Context Processors ───────────────────────────────────────────────
    register_context_processors(app)

    # ─── Create Upload Folder ─────────────────────────────────────────────
    covers_dir = os.path.join(app.root_path, 'static', 'images', 'covers')
    os.makedirs(covers_dir, exist_ok=True)

    # ─── Database Init & Seed ─────────────────────────────────────────────
    with app.app_context():
        try:
            db.create_all(checkfirst=True)
            seed_initial_data(app)
        except Exception as e:
            app.logger.warning(f"Database initialization skipped: {e}")

return app

def register_error_handlers(app):
    """Register custom error page handlers."""

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('errors/500.html'), 500


def register_context_processors(app):
    """Inject common variables into every template context."""

    @app.context_processor
    def inject_globals():
        from app.models.borrow import Borrow
        from app.models.book import Book
        from flask_login import current_user

        unread_count = 0
        overdue_count = 0

        if current_user.is_authenticated:
            try:
                if current_user.role in ('admin', 'librarian'):
                    overdue_count = Borrow.query.filter(
                        Borrow.status == 'borrowed',
                        Borrow.due_date < db.func.current_date()
                    ).count()
                else:
                    overdue_count = Borrow.query.filter_by(
                        user_id=current_user.id, status='borrowed'
                    ).filter(
                        Borrow.due_date < db.func.current_date()
                    ).count()
            except Exception:
                overdue_count = 0

        return {
            'overdue_count': overdue_count,
            'app_name': 'LibraTrack',
        }


def seed_initial_data(app):
    """
    Create the default admin account and sample categories on first run.
    Safe to call repeatedly – only inserts if records don't exist.
    """
    from app.models.user import User
    from app.models.book import Category
    from app import bcrypt as _bcrypt

    # Create admin user if not present
    if not User.query.filter_by(email=app.config['ADMIN_EMAIL']).first():
        admin = User(
            first_name=app.config.get('ADMIN_FIRST_NAME', 'System'),
            last_name=app.config.get('ADMIN_LAST_NAME', 'Administrator'),
            email=app.config['ADMIN_EMAIL'],
            password_hash=_bcrypt.generate_password_hash(
                app.config['ADMIN_PASSWORD']
            ).decode('utf-8'),
            role='admin',
            is_active=True,
            member_id='ADM-0001',
        )
        db.session.add(admin)

    # Seed default categories
    default_categories = [
        ('Fiction', 'Novels, short stories, and other imaginative works'),
        ('Non-Fiction', 'Factual books including biographies and history'),
        ('Science & Technology', 'Books on science, engineering, and tech'),
        ('Computer Science', 'Programming, algorithms, and software'),
        ('Mathematics', 'Pure and applied mathematics'),
        ('History', 'Historical accounts and analysis'),
        ('Philosophy', 'Philosophical works and critical thinking'),
        ('Psychology', 'Human behaviour and mental processes'),
        ('Business & Economics', 'Finance, management, and economics'),
        ('Reference', 'Encyclopaedias, dictionaries, and atlases'),
    ]

    for name, desc in default_categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name, description=desc))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
