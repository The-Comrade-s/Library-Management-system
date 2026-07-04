"""
app/models/user.py
==================
User model with role-based access control.
"""

from datetime import datetime, date
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Identity
    member_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

    # Authentication
    password_hash = db.Column(db.String(255), nullable=False)

    # Profile
    profile_picture = db.Column(
        db.String(255),
        default="default_avatar.png"
    )
    date_of_birth = db.Column(db.Date)

    # Role
    role = db.Column(
        db.Enum("admin", "librarian", "member", name="user_roles"),
        nullable=False,
        default="member"
    )

    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Password Reset
    reset_token = db.Column(db.String(255))
    reset_token_expiry = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    last_login = db.Column(db.DateTime)

    # ==========================
    # Relationships
    # ==========================

    # Books borrowed by this user
    borrows = db.relationship(
        "Borrow",
        foreign_keys="Borrow.user_id",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # Books issued by this librarian/admin
    issued_borrows = db.relationship(
        "Borrow",
        foreign_keys="Borrow.issued_by",
        lazy="dynamic"
    )

    # Fines belonging to this user
    fines = db.relationship(
        "Fine",
        foreign_keys="Fine.user_id",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    # Fines collected by librarian/admin
    collected_fines = db.relationship(
        "Fine",
        foreign_keys="Fine.paid_by",
        lazy="dynamic"
    )

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_librarian(self):
        return self.role == "librarian"

    @property
    def is_member(self):
        return self.role == "member"

    @property
    def can_manage(self):
        return self.role in ("admin", "librarian")

    @property
    def active_borrows_count(self):
        return self.borrows.filter_by(status="borrowed").count()

    @property
    def total_unpaid_fines(self):
        from app.models.fine import Fine

        total = db.session.query(
            db.func.sum(Fine.amount)
        ).filter(
            Fine.user_id == self.id,
            Fine.status == "unpaid"
        ).scalar()

        return float(total) if total else 0.0

    @property
    def age(self):
        if not self.date_of_birth:
            return None

        today = date.today()

        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    @staticmethod
    def generate_member_id():
        last_user = User.query.order_by(User.id.desc()).first()
        next_id = last_user.id + 1 if last_user else 1
        return f"MEM-{next_id:04d}"

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    def __repr__(self):
        return (
            f"<User {self.member_id}: "
            f"{self.full_name} ({self.role})>"
        )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
