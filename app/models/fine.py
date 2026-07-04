"""
app/models/fine.py - Fine Model
==================================
Manages overdue fines linked to borrow transactions.
Fine → Borrow: One-to-one
Fine → User: Many-to-one
Save at: LMS/app/models/fine.py
"""

from datetime import datetime
from app import db


class Fine(db.Model):
    """
    Represents an overdue fine for a borrowing transaction.
    Automatically calculated based on days overdue × daily rate.
    """
    __tablename__ = 'fines'

    # ─── Primary Key ─────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ─── Foreign Keys ─────────────────────────────────────────────────────
    borrow_id = db.Column(db.Integer, db.ForeignKey('borrows.id'),
                          nullable=False, unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False, index=True)

    # ─── Financial ────────────────────────────────────────────────────────
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    days_overdue = db.Column(db.Integer, nullable=False, default=0)
    daily_rate = db.Column(db.Numeric(10, 2), nullable=False, default=0.50)

    # ─── Status ──────────────────────────────────────────────────────────
    status = db.Column(
        db.Enum('unpaid', 'paid', 'waived', name='fine_status'),
        nullable=False,
        default='unpaid'
    )

    # ─── Payment Details ─────────────────────────────────────────────────
    paid_at = db.Column(db.DateTime, nullable=True)
    paid_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    receipt_number = db.Column(db.String(50), nullable=True, unique=True)
    notes = db.Column(db.Text, nullable=True)

    # ─── Timestamps ───────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)

    # ─── Relationships ────────────────────────────────────────────────────
    borrow = db.relationship('Borrow', back_populates='fine')
    user = db.relationship('User', back_populates='fines',
                           foreign_keys=[user_id])
    collector = db.relationship('User', foreign_keys=[paid_by])

    # ─── Properties ──────────────────────────────────────────────────────
    @property
    def amount_float(self):
        return float(self.amount)

    @property
    def is_paid(self):
        return self.status == 'paid'

    @property
    def is_waived(self):
        return self.status == 'waived'

    # ─── Methods ─────────────────────────────────────────────────────────
    def mark_paid(self, paid_by_id, payment_method='cash'):
        """Mark this fine as paid and generate a receipt number."""
        import random
        import string
        self.status = 'paid'
        self.paid_at = datetime.utcnow()
        self.paid_by = paid_by_id
        self.payment_method = payment_method
        self.receipt_number = 'RCP-' + ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )

    def mark_waived(self, by_user_id, reason=None):
        """Waive the fine (admin action)."""
        self.status = 'waived'
        self.paid_at = datetime.utcnow()
        self.paid_by = by_user_id
        self.notes = reason or 'Waived by administrator'

    @classmethod
    def create_for_borrow(cls, borrow, daily_rate=0.50):
        """Factory method to create a fine for an overdue borrow."""
        days = (borrow.days_overdue or 0)
        amount = round(days * daily_rate, 2)
        return cls(
            borrow_id=borrow.id,
            user_id=borrow.user_id,
            amount=amount,
            days_overdue=days,
            daily_rate=daily_rate,
            status='unpaid'
        )

    def __repr__(self):
        return (f'<Fine #{self.id}: ${self.amount} '
                f'[{self.status}] for Borrow #{self.borrow_id}>')
