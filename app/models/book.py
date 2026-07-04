"""
app/models/book.py - Book & Category Models
=============================================
Defines Book and Category database models.
Book → Category: Many-to-one
Book → Borrow: One-to-many
Save at: LMS/app/models/book.py
"""

from datetime import datetime
from app import db


class Category(db.Model):
    """Book categories / genres."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ─── Relationships ────────────────────────────────────────────────────
    books = db.relationship('Book', back_populates='category',
                            lazy='dynamic')

    @property
    def book_count(self):
        return self.books.count()

    def __repr__(self):
        return f'<Category {self.name}>'


class Book(db.Model):
    """
    Book model representing a physical library book.
    Tracks title, author, ISBN, availability, and cover image.
    """
    __tablename__ = 'books'

    # ─── Primary Key ─────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ─── Bibliographic Information ────────────────────────────────────────
    title = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(255), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=True, index=True)
    publisher = db.Column(db.String(150), nullable=True)
    publication_year = db.Column(db.Integer, nullable=True)
    edition = db.Column(db.String(50), nullable=True)
    language = db.Column(db.String(50), nullable=True, default='English')
    pages = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)

    # ─── Classification ───────────────────────────────────────────────────
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'),
                            nullable=True, index=True)
    barcode = db.Column(db.String(50), unique=True, nullable=True, index=True)
    shelf_location = db.Column(db.String(50), nullable=True)

    # ─── Inventory ────────────────────────────────────────────────────────
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)

    # ─── Media ───────────────────────────────────────────────────────────
    cover_image = db.Column(db.String(255), nullable=True,
                            default='default_cover.jpg')

    # ─── Status ──────────────────────────────────────────────────────────
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relationships ────────────────────────────────────────────────────
    category = db.relationship('Category', back_populates='books')
    borrows = db.relationship('Borrow', back_populates='book',
                              lazy='dynamic', cascade='all, delete-orphan')

    # ─── Properties ──────────────────────────────────────────────────────
    @property
    def is_available(self):
        return self.available_copies > 0 and self.is_active

    @property
    def borrow_count(self):
        """Total number of times this book has been borrowed."""
        return self.borrows.count()

    @property
    def current_borrowers(self):
        """Users who currently have this book."""
        return self.borrows.filter_by(status='borrowed').all()

    @property
    def availability_status(self):
        if not self.is_active:
            return 'Inactive'
        if self.available_copies == 0:
            return 'Fully Borrowed'
        if self.available_copies < self.total_copies:
            return 'Partially Available'
        return 'Available'

    @property
    def cover_url(self):
        if self.cover_image:
            return f'/static/images/covers/{self.cover_image}'
        return '/static/images/default_cover.jpg'

    # ─── Methods ─────────────────────────────────────────────────────────
    def checkout(self):
        """Reduce available copies when borrowed."""
        if self.available_copies > 0:
            self.available_copies -= 1
            return True
        return False

    def checkin(self):
        """Restore available copies when returned."""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False

    def generate_barcode(self):
        """Generate a unique barcode if none exists."""
        if not self.barcode:
            self.barcode = f'LIB-{self.id:06d}'

    def __repr__(self):
        return f'<Book "{self.title}" by {self.author}>'
