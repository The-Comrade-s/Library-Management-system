"""
app/reports/routes.py - Reports & Analytics
Save at: LMS/app/reports/routes.py
"""

from datetime import date, timedelta
from flask import render_template, abort, request, make_response
from flask_login import login_required, current_user
from sqlalchemy import func
from app.reports import reports_bp
from app.models.book import Book, Category
from app.models.borrow import Borrow
from app.models.fine import Fine
from app.models.user import User
from app import db


def staff_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@reports_bp.route('/')
@login_required
@staff_required
def index():
    return render_template('reports/index.html', title='Reports')


@reports_bp.route('/borrowed')
@login_required
@staff_required
def borrowed_report():
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')

    query = Borrow.query.filter_by(status='borrowed')
    if date_from:
        query = query.filter(Borrow.borrow_date >= date_from)
    if date_to:
        query = query.filter(Borrow.borrow_date <= date_to)

    borrows = query.order_by(Borrow.borrow_date.desc()).paginate(
        page=page, per_page=25, error_out=False)
    return render_template('reports/borrowed.html',
                           borrows=borrows, date_from=date_from,
                           date_to=date_to, title='Borrowed Books Report')


@reports_bp.route('/overdue')
@login_required
@staff_required
def overdue_report():
    today = date.today()
    overdue = Borrow.query.filter(
        Borrow.status == 'borrowed',
        Borrow.due_date < today
    ).order_by(Borrow.due_date.asc()).all()

    total_potential_fines = sum(b.calculated_fine for b in overdue)
    return render_template('reports/overdue.html',
                           overdue=overdue,
                           total_potential_fines=total_potential_fines,
                           title='Overdue Books Report')


@reports_bp.route('/popular-books')
@login_required
@staff_required
def popular_books():
    popular = db.session.query(
        Book,
        func.count(Borrow.id).label('borrow_count')
    ).join(Borrow).group_by(Book.id).order_by(
        func.count(Borrow.id).desc()
    ).limit(20).all()
    return render_template('reports/popular.html',
                           popular=popular, title='Popular Books')


@reports_bp.route('/active-members')
@login_required
@staff_required
def active_members():
    members = db.session.query(
        User,
        func.count(Borrow.id).label('borrow_count')
    ).join(Borrow, User.id == Borrow.user_id).filter(
        User.role == 'member'
    ).group_by(User.id).order_by(
        func.count(Borrow.id).desc()
    ).limit(20).all()
    return render_template('reports/active_members.html',
                           members=members, title='Most Active Members')


@reports_bp.route('/fines-summary')
@login_required
@staff_required
def fines_summary():
    stats = {
        'total_unpaid': db.session.query(func.sum(Fine.amount))
                          .filter_by(status='unpaid').scalar() or 0,
        'total_paid': db.session.query(func.sum(Fine.amount))
                        .filter_by(status='paid').scalar() or 0,
        'total_waived': db.session.query(func.sum(Fine.amount))
                          .filter_by(status='waived').scalar() or 0,
        'count_unpaid': Fine.query.filter_by(status='unpaid').count(),
        'count_paid': Fine.query.filter_by(status='paid').count(),
        'count_waived': Fine.query.filter_by(status='waived').count(),
    }
    recent_paid = Fine.query.filter_by(status='paid').order_by(
        Fine.paid_at.desc()).limit(20).all()
    return render_template('reports/fines_summary.html',
                           stats=stats, recent_paid=recent_paid,
                           title='Fines Summary')


@reports_bp.route('/inventory')
@login_required
@staff_required
def inventory():
    books = Book.query.order_by(Book.title).all()
    total_copies = sum(b.total_copies for b in books)
    available = sum(b.available_copies for b in books)
    borrowed = total_copies - available
    return render_template('reports/inventory.html',
                           books=books,
                           total_copies=total_copies,
                           available=available,
                           borrowed=borrowed,
                           title='Inventory Report')


@reports_bp.route('/export/overdue-csv')
@login_required
@staff_required
def export_overdue_csv():
    """Export overdue books as CSV."""
    import csv
    import io
    today = date.today()
    overdue = Borrow.query.filter(
        Borrow.status == 'borrowed',
        Borrow.due_date < today
    ).order_by(Borrow.due_date.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Member ID', 'Member Name', 'Email', 'Book Title',
                     'Author', 'ISBN', 'Borrow Date', 'Due Date',
                     'Days Overdue', 'Fine Amount'])
    for b in overdue:
        writer.writerow([
            b.user.member_id, b.user.full_name, b.user.email,
            b.book.title, b.book.author, b.book.isbn or '',
            b.borrow_date.strftime('%Y-%m-%d'),
            b.due_date.strftime('%Y-%m-%d'),
            b.days_overdue, f'${b.calculated_fine:.2f}'
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=overdue_books.csv'
    response.headers['Content-type'] = 'text/csv'
    return response
