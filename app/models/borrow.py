"""
app/models/borrow.py
====================
Borrow Model
Tracks borrowing transactions.
"""

from datetime import datetime, date, timedelta
from flask import current_app
from app import db


class Borrow(db.Model):
    __tablename__ = "borrows"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    book_id = db.Column(
        db.Integer,
        db.ForeignKey("books.id"),
        nullable=False,
        index=True,
    )

    issued_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Dates
    borrow_date = db.Column(
        db.Date,
        default=date.today,
        nullable=False,
    )

    due_date = db.Column(
        db.Date,
        nullable=False,
    )

    return_date = db.Column(db.Date)

    # Status
    status = db.Column(
        db.Enum(
            "borrowed",
            "returned",
            "overdue",
            name="borrow_status",
        ),
        default="borrowed",
        nullable=False,
    )

    # Extra
    notes = db.Column(db.Text)

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

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="borrows",
    )

    issuer = db.relationship(
        "User",
        foreign_keys=[issued_by],
        back_populates="issued_borrows",
    )

    book = db.relationship(
        "Book",
        back_populates="borrows",
    )

    fine = db.relationship(
        "Fine",
        back_populates="borrow",
        uselist=False,
        cascade="all, delete-orphan",
    )

    # ==========================
    # Properties
    # ==========================

    @property
    def is_overdue(self):
        if self.status == "returned":
            return False
        return date.today() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days

    @property
    def days_remaining(self):
        if self.status == "returned":
            return 0
        return max(0, (self.due_date - date.today()).days)

    @property
    def calculated_fine(self):
        if not self.is_overdue:
            return 0.0

        rate = current_app.config.get(
            "DAILY_FINE_RATE",
            0.50,
        )

        return round(self.days_overdue * rate, 2)

    @property
    def status_display(self):
        if self.is_overdue and self.status == "borrowed":
            return "overdue"
        return self.status

    @property
    def borrow_duration(self):
        end = self.return_date or date.today()
        return (end - self.borrow_date).days

    # ==========================
    # Factory
    # ==========================

    @classmethod
    def create_borrow(
        cls,
        user_id,
        book_id,
        issued_by_id=None,
    ):
        duration = current_app.config.get(
            "BORROW_DURATION_DAYS",
            14,
        )

        return cls(
            user_id=user_id,
            book_id=book_id,
            issued_by=issued_by_id,
            borrow_date=date.today(),
            due_date=date.today() + timedelta(days=duration),
            status="borrowed",
        )

    def __repr__(self):
        return (
            f"<Borrow #{self.id}: "
            f"User {self.user_id} -> "
            f"Book {self.book_id} "
            f"[{self.status}]>"
        )
