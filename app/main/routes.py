"""
app/main/routes.py - Main / Home Routes
Save at: LMS/app/main/routes.py
"""

from flask import render_template, redirect, url_for
from flask_login import current_user
from app.main import main_bp
from app.models.book import Book, Category
from app.models.borrow import Borrow
from app.models.user import User
from app import db


@main_bp.route('/')
def index():
    """Public landing page with library stats."""
    if current_user.is_authenticated:
        if current_user.can_manage:
            return redirect(url_for('dashboard.admin_dashboard'))
        return redirect(url_for('dashboard.member_dashboard'))

    # Public stats for landing page
    stats = {
        'total_books': Book.query.filter_by(is_active=True).count(),
        'total_members': User.query.filter_by(role='member', is_active=True).count(),
        'total_borrows': Borrow.query.count(),
        'total_categories': Category.query.count(),
    }
    featured_books = Book.query.filter_by(is_active=True).order_by(
        Book.created_at.desc()
    ).limit(8).all()

    return render_template('main/index.html',
                           stats=stats,
                           featured_books=featured_books)


@main_bp.route('/about')
def about():
    return render_template('main/about.html')


@main_bp.route('/catalogue')
def catalogue():
    """Public book catalogue (no login required)."""
    books = Book.query.filter_by(is_active=True).order_by(Book.title).paginate(
        page=1, per_page=12, error_out=False
    )
    categories = Category.query.order_by(Category.name).all()
    return render_template('main/catalogue.html',
                           books=books, categories=categories)
