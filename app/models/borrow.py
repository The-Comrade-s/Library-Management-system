"""
app/models/borrow.py - Borrow Model
=====================================
Tracks book borrowing transactions including due dates and return status.
Borrow → User: Many-to-one
Borrow → Book: Many-to-one
Borrow → Fine: One-to-one
Save at: LMS/app/models/borrow.py
"""

from datetime import datetime, date, timedelta
from app import db
from flask import current_app


class Borrow(db.Model):
    """
    Represents a single borrowing transaction.
    Status lifecycle: borrowed → returned (or overdue)
    """
    __tablename__ = 'borrows'

    # ─── Primary Key ─────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ─── Foreign Keys ─────────────────────────────────────────────────────
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'),
                        nullable=False, index=True)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'),
                          nullable=True)  # Librarian/admin who issued

    # ─── Dates ───────────────────────────────────────────────────────────
    borrow_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)  # Null until returned

    # ─── Status ──────────────────────────────────────────────────────────
    status = db.Column(
        db.Enum('borrowed', 'returned', 'overdue', name='borrow_status'),
        nullable=False,
        default='borrowed'
    )

    # ─── Notes ───────────────────────────────────────────────────────────
    notes = db.Column(db.Text, nullable=True)

    # ─── Timestamps ───────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relationships ────────────────────────────────────────────────────
    user = db.relationship('User', back_populates='borrows',
                           foreign_keys=[user_id])
    book = db.relationship('Book', back_populates='borrows')
    fine = db.relationship('Fine', back_populates='borrow',
                           uselist=False, cascade='all, delete-orphan')
    issuer = db.relationship('User', foreign_keys=[issued_by])

    # ─── Properties ──────────────────────────────────────────────────────
    @property
    def is_overdue(self):
        if self.status == 'returned':
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    @property
    def days_remaining(self):
        if self.status == 'returned':
            return 0
        delta = self.due_date - date.today()
        return max(0, delta.days)

    @property
    def calculated_fine(self):
        """Calculate the fine amount based on overdue days."""
        if not self.is_overdue:
            return 0.0
        rate = current_app.config.get('DAILY_FINE_RATE', 0.50)
        return round(self.days_overdue * rate, 2)

    @property
    def status_display(self):
        if self.is_overdue and self.status == 'borrowed':
            return 'overdue'
        return self.status

    @property
    def borrow_duration(self):
        """How many days the book was/has been borrowed."""
        end = self.return_date or date.today()
        return (end - self.borrow_date).days

    # ─── Class Methods ────────────────────────────────────────────────────
    @classmethod
    def create_borrow(cls, user_id, book_id, issued_by_id=None):
        """Factory method to create a new borrow record."""
        from flask import current_app
        duration = current_app.config.get('BORROW_DURATION_DAYS', 14)
        return cls(
            user_id=user_id,
            book_id=book_id,
            issued_by=issued_by_id,
            borrow_date=date.today(),
            due_date=date.today() + timedelta(days=duration),
            status='borrowed'
        )

    def __repr__(self):
        return (f'<Borrow #{self.id}: User {self.user_id} → '
                f'Book {self.book_id} [{self.status}]>')
