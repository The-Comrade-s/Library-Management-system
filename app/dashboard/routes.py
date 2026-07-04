"""
app/dashboard/routes.py - Dashboard Routes
Save at: LMS/app/dashboard/routes.py
"""

from datetime import date, timedelta
from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func
from app.dashboard import dashboard_bp
from app.models.user import User
from app.models.book import Book, Category
from app.models.borrow import Borrow
from app.models.fine import Fine
from app import db


def admin_required(f):
    from functools import wraps
    from flask import abort
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@dashboard_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    # Core stats
    stats = {
        'total_books': Book.query.filter_by(is_active=True).count(),
        'available_books': db.session.query(func.sum(Book.available_copies))
                             .filter_by(is_active=True).scalar() or 0,
        'borrowed_books': Borrow.query.filter_by(status='borrowed').count(),
        'overdue_books': Borrow.query.filter(
            Borrow.status == 'borrowed',
            Borrow.due_date < today
        ).count(),
        'total_users': User.query.filter_by(role='member', is_active=True).count(),
        'total_fines': db.session.query(func.sum(Fine.amount))
                         .filter_by(status='unpaid').scalar() or 0,
        'total_categories': Category.query.count(),
        'fines_collected': db.session.query(func.sum(Fine.amount))
                              .filter_by(status='paid').scalar() or 0,
    }

    # Recent borrows
    recent_borrows = Borrow.query.order_by(Borrow.created_at.desc()).limit(8).all()

    # Overdue list
    overdue_borrows = Borrow.query.filter(
        Borrow.status == 'borrowed',
        Borrow.due_date < today
    ).order_by(Borrow.due_date.asc()).limit(10).all()

    # Monthly borrow activity (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 30))
        month_start = month_start.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        count = Borrow.query.filter(
            Borrow.borrow_date >= month_start,
            Borrow.borrow_date < month_end
        ).count()
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'count': count
        })

    # Top 5 popular books
    popular_books = db.session.query(
        Book.title, func.count(Borrow.id).label('borrow_count')
    ).join(Borrow).group_by(Book.id, Book.title).order_by(
        func.count(Borrow.id).desc()
    ).limit(5).all()

    # Category distribution
    category_stats = db.session.query(
        Category.name, func.count(Book.id).label('count')
    ).join(Book, isouter=True).group_by(Category.id, Category.name).all()

    return render_template('dashboard/admin.html',
                           stats=stats,
                           recent_borrows=recent_borrows,
                           overdue_borrows=overdue_borrows,
                           monthly_data=monthly_data,
                           popular_books=popular_books,
                           category_stats=category_stats,
                           title='Admin Dashboard')


@dashboard_bp.route('/member')
@login_required
def member_dashboard():
    if current_user.can_manage:
        return redirect(url_for('dashboard.admin_dashboard'))

    today = date.today()
    active_borrows = Borrow.query.filter_by(
        user_id=current_user.id, status='borrowed'
    ).order_by(Borrow.due_date.asc()).all()

    borrow_history = Borrow.query.filter_by(
        user_id=current_user.id
    ).order_by(Borrow.created_at.desc()).limit(10).all()

    unpaid_fines = Fine.query.filter_by(
        user_id=current_user.id, status='unpaid'
    ).all()

    overdue = [b for b in active_borrows if b.is_overdue]
    due_soon = [b for b in active_borrows
                if not b.is_overdue and b.days_remaining <= 3]

    stats = {
        'active_borrows': len(active_borrows),
        'total_borrowed': Borrow.query.filter_by(user_id=current_user.id).count(),
        'total_returned': Borrow.query.filter_by(
            user_id=current_user.id, status='returned').count(),
        'unpaid_fines': sum(float(f.amount) for f in unpaid_fines),
    }

    return render_template('dashboard/member.html',
                           active_borrows=active_borrows,
                           borrow_history=borrow_history,
                           unpaid_fines=unpaid_fines,
                           overdue=overdue,
                           due_soon=due_soon,
                           stats=stats,
                           title='My Dashboard')
