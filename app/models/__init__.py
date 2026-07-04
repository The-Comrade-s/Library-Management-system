"""
app/models/__init__.py
Exports all models so they are discovered by SQLAlchemy and Flask-Migrate.
"""

from app.models.user import User
from app.models.book import Book, Category
from app.models.borrow import Borrow
from app.models.fine import Fine

__all__ = ['User', 'Book', 'Category', 'Borrow', 'Fine']
