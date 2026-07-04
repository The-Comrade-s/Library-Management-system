"""
app/models/fine.py
==================
Fine Model
Represents overdue fines for borrowed books.
"""

from datetime import datetime
from app import db


class Fine(db.Model):
    __tablename__ = "fines"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Foreign Keys
    borrow_id = db.Column(
        db.Integer,
        db.ForeignKey("borrows.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    paid_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    # Financial Information
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    days_overdue = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    daily_rate = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0.50,
    )

    # Status
    status = db.Column(
        db.Enum(
            "unpaid",
            "paid",
            "waived",
            name="fine_status",
        ),
        nullable=False,
        default="unpaid",
    )

    # Payment Details
    paid_at = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    receipt_number = db.Column(db.String(50), unique=True)
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

    borrow = db.relationship(
        "Borrow",
        back_populates="fine",
    )

    user = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="fines",
    )

    collector = db.relationship(
        "User",
        foreign_keys=[paid_by],
        back_populates="collected_fines",
    )

    # ==========================
    # Properties
    # ==========================

    @property
    def amount_float(self):
        return float(self.amount)

    @property
    def is_paid(self):
        return self.status == "paid"

    @property
    def is_waived(self):
        return self.status == "waived"

    # ==========================
    # Methods
    # ==========================

    def mark_paid(self, paid_by_id, payment_method="cash"):
        import random
        import string

        self.status = "paid"
        self.paid_at = datetime.utcnow()
        self.paid_by = paid_by_id
        self.payment_method = payment_method

        self.receipt_number = "RCP-" + "".join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=8,
            )
        )

    def mark_waived(self, by_user_id, reason=None):
        self.status = "waived"
        self.paid_at = datetime.utcnow()
        self.paid_by = by_user_id
        self.notes = reason or "Waived by administrator"

    @classmethod
    def create_for_borrow(
        cls,
        borrow,
        daily_rate=0.50,
    ):
        days = borrow.days_overdue or 0
        amount = round(days * daily_rate, 2)

        return cls(
            borrow_id=borrow.id,
            user_id=borrow.user_id,
            amount=amount,
            days_overdue=days,
            daily_rate=daily_rate,
            status="unpaid",
        )

    def __repr__(self):
        return (
            f"<Fine #{self.id}: "
            f"${self.amount} "
            f"[{self.status}] "
            f"Borrow #{self.borrow_id}>"
        )
