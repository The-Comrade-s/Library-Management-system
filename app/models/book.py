"""
app/models/book.py
==================
Book & Category Models
"""

from datetime import datetime
from app import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    books = db.relationship(
        "Book",
        back_populates="category",
        lazy="dynamic",
    )

    @property
    def book_count(self):
        return self.books.count()

    def __repr__(self):
        return f"<Category {self.name}>"


class Book(db.Model):
    __tablename__ = "books"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Bibliographic Information
    title = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(255), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, index=True)
    publisher = db.Column(db.String(150))
    publication_year = db.Column(db.Integer)
    edition = db.Column(db.String(50))
    language = db.Column(
        db.String(50),
        default="English",
    )
    pages = db.Column(db.Integer)
    description = db.Column(db.Text)

    # Classification
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        index=True,
    )

    barcode = db.Column(
        db.String(50),
        unique=True,
        index=True,
    )

    shelf_location = db.Column(db.String(50))

    # Inventory
    total_copies = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    available_copies = db.Column(
        db.Integer,
        nullable=False,
        default=1,
    )

    # Media
    cover_image = db.Column(
        db.String(255),
        default="default_cover.jpg",
    )

    # Status
    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False,
    )

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ==========================
    # Relationships
    # ==========================

    category = db.relationship(
        "Category",
        back_populates="books",
    )

    borrows = db.relationship(
        "Borrow",
        back_populates="book",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ==========================
    # Properties
    # ==========================

    @property
    def is_available(self):
        return self.is_active and self.available_copies > 0

    @property
    def borrow_count(self):
        return self.borrows.count()

    @property
    def current_borrowers(self):
        return self.borrows.filter_by(status="borrowed").all()

    @property
    def availability_status(self):
        if not self.is_active:
            return "Inactive"

        if self.available_copies == 0:
            return "Fully Borrowed"

        if self.available_copies < self.total_copies:
            return "Partially Available"

        return "Available"

    @property
    def cover_url(self):
        if self.cover_image:
            return f"/static/images/covers/{self.cover_image}"
        return "/static/images/default_cover.jpg"

    # ==========================
    # Methods
    # ==========================

    def checkout(self):
        if self.available_copies > 0:
            self.available_copies -= 1
            return True
        return False

    def checkin(self):
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            return True
        return False

    def generate_barcode(self):
        if not self.barcode:
            self.barcode = f"LIB-{self.id:06d}"

    def __repr__(self):
        return f"<Book '{self.title}' by {self.author}>"
