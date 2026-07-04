"""
app/models/user.py - User Model
=================================
Defines the User database model with role-based access control.
Relationships: one-to-many with Borrow and Fine.
Save at: LMS/app/models/user.py
"""

from datetime import datetime, date
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    """
    User model supporting three roles: admin, librarian, member.
    Inherits UserMixin to integrate with Flask-Login.
    """
    __tablename__ = 'users'

    # ─── Primary Key ─────────────────────────────────────────────────────
    id = db.Column(db.Integer, primary_key=True)

    # ─── Identity ────────────────────────────────────────────────────────
    member_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)

    # ─── Authentication ───────────────────────────────────────────────────
    password_hash = db.Column(db.String(255), nullable=False)

    # ─── Profile ─────────────────────────────────────────────────────────
    profile_picture = db.Column(db.String(255), nullable=True,
                                default='default_avatar.png')
    date_of_birth = db.Column(db.Date, nullable=True)

    # ─── Role & Status ────────────────────────────────────────────────────
    role = db.Column(db.Enum('admin', 'librarian', 'member', name='user_roles'),
                     nullable=False, default='member')
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    # ─── Timestamps ───────────────────────────────────────────────────────
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    # ─── Password Reset ───────────────────────────────────────────────────
    reset_token = db.Column(db.String(255), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # ─── Relationships ────────────────────────────────────────────────────
    borrows = db.relationship('Borrow', back_populates='user',
                              lazy='dynamic', cascade='all, delete-orphan')
    fines = db.relationship('Fine', back_populates='user',
                            lazy='dynamic', cascade='all, delete-orphan')

    # ─── Properties ──────────────────────────────────────────────────────
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_librarian(self):
        return self.role == 'librarian'

    @property
    def is_member(self):
        return self.role == 'member'

    @property
    def can_manage(self):
        """Admin and librarian can manage the library."""
        return self.role in ('admin', 'librarian')

    @property
    def active_borrows_count(self):
        return self.borrows.filter_by(status='borrowed').count()

    @property
    def total_unpaid_fines(self):
        from app.models.fine import Fine
        result = db.session.query(db.func.sum(Fine.amount)).filter(
            Fine.user_id == self.id,
            Fine.status == 'unpaid'
        ).scalar()
        return float(result) if result else 0.0

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) <
                (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    # ─── Methods ─────────────────────────────────────────────────────────
    @staticmethod
    def generate_member_id():
        """Generate a unique member ID like MEM-0042."""
        last_user = User.query.order_by(User.id.desc()).first()
        next_id = (last_user.id + 1) if last_user else 1
        return f"MEM-{next_id:04d}"

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return f'<User {self.member_id}: {self.full_name} ({self.role})>'


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login callback to reload the user object from the user_id in the session.
    Called on every request for authenticated users.
    """
    return db.session.get(User, int(user_id))
