"""
app/borrow/routes.py - Borrowing System Routes
Save at: LMS/app/borrow/routes.py
"""

from datetime import date
from flask import (render_template, redirect, url_for, flash,
                   request, abort, current_app, jsonify)
from flask_login import login_required, current_user
from app.borrow import borrow_bp
from app.models.book import Book
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


# ─── Borrow a Book ────────────────────────────────────────────────────────────

@borrow_bp.route('/issue/<int:book_id>', methods=['POST'])
@login_required
@staff_required
def issue_book(book_id):
    """Staff issues a book to a member."""
    book = Book.query.get_or_404(book_id)
    user_id = request.form.get('user_id', type=int)

    if not user_id:
        flash('Please select a member.', 'danger')
        return redirect(url_for('books.book_detail', book_id=book_id))

    member = User.query.get_or_404(user_id)

    # Validation
    if not book.is_available:
        flash('No copies available to borrow.', 'danger')
        return redirect(url_for('books.book_detail', book_id=book_id))

    max_books = current_app.config.get('MAX_BOOKS_PER_USER', 5)
    if member.active_borrows_count >= max_books:
        flash(f'{member.full_name} already has {max_books} books. Return one first.', 'danger')
        return redirect(url_for('books.book_detail', book_id=book_id))

    if member.total_unpaid_fines > 0:
        flash(f'{member.full_name} has unpaid fines of ${member.total_unpaid_fines:.2f}. '
              f'Please clear fines before borrowing.', 'warning')
        return redirect(url_for('books.book_detail', book_id=book_id))

    existing = Borrow.query.filter_by(
        user_id=user_id, book_id=book_id, status='borrowed'
    ).first()
    if existing:
        flash(f'{member.full_name} already has this book borrowed.', 'warning')
        return redirect(url_for('books.book_detail', book_id=book_id))

    # Create borrow
    borrow = Borrow.create_borrow(user_id, book_id, current_user.id)
    book.checkout()
    db.session.add(borrow)
    db.session.commit()

    flash(f'"{book.title}" issued to {member.full_name}. '
          f'Due: {borrow.due_date.strftime("%d %b %Y")}', 'success')
    return redirect(url_for('books.book_detail', book_id=book_id))


@borrow_bp.route('/self-borrow/<int:book_id>', methods=['POST'])
@login_required
def self_borrow(book_id):
    """Member requests to borrow a book (creates pending request)."""
    book = Book.query.get_or_404(book_id)

    if not book.is_available:
        flash('No copies of this book are currently available.', 'danger')
        return redirect(url_for('books.book_detail', book_id=book_id))

    max_books = current_app.config.get('MAX_BOOKS_PER_USER', 5)
    if current_user.active_borrows_count >= max_books:
        flash(f'You can borrow a maximum of {max_books} books at once.', 'warning')
        return redirect(url_for('books.book_detail', book_id=book_id))

    if current_user.total_unpaid_fines > 0:
        flash('You have unpaid fines. Please clear them before borrowing.', 'warning')
        return redirect(url_for('dashboard.member_dashboard'))

    existing = Borrow.query.filter_by(
        user_id=current_user.id, book_id=book_id, status='borrowed'
    ).first()
    if existing:
        flash('You already have this book borrowed.', 'warning')
        return redirect(url_for('books.book_detail', book_id=book_id))

    borrow = Borrow.create_borrow(current_user.id, book_id)
    book.checkout()
    db.session.add(borrow)
    db.session.commit()

    flash(f'You have borrowed "{book.title}". '
          f'Please return by {borrow.due_date.strftime("%d %b %Y")}.', 'success')
    return redirect(url_for('dashboard.member_dashboard'))


# ─── Return a Book ────────────────────────────────────────────────────────────

@borrow_bp.route('/return/<int:borrow_id>', methods=['POST'])
@login_required
@staff_required
def return_book(borrow_id):
    """Staff processes a book return."""
    borrow = Borrow.query.get_or_404(borrow_id)

    if borrow.status == 'returned':
        flash('This book has already been returned.', 'warning')
        return redirect(url_for('borrow.all_borrows'))

    borrow.return_date = date.today()
    borrow.status = 'returned'
    borrow.book.checkin()

    # Auto-create fine if overdue
    fine_amount = 0.0
    if borrow.is_overdue:
        rate = current_app.config.get('DAILY_FINE_RATE', 0.50)
        fine = Fine.create_for_borrow(borrow, rate)
        db.session.add(fine)
        fine_amount = float(fine.amount)

    db.session.commit()

    msg = f'"{borrow.book.title}" returned by {borrow.user.full_name}.'
    if fine_amount > 0:
        msg += f' Fine applied: ${fine_amount:.2f}'
    flash(msg, 'success' if fine_amount == 0 else 'warning')
    return redirect(request.referrer or url_for('borrow.all_borrows'))


# ─── Borrow Lists ─────────────────────────────────────────────────────────────

@borrow_bp.route('/')
@login_required
@staff_required
def all_borrows():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    q = request.args.get('q', '').strip()

    query = Borrow.query

    if status == 'borrowed':
        query = query.filter_by(status='borrowed')
    elif status == 'returned':
        query = query.filter_by(status='returned')
    elif status == 'overdue':
        query = query.filter(
            Borrow.status == 'borrowed',
            Borrow.due_date < date.today()
        )

    if q:
        query = query.join(User).join(Book).filter(
            db.or_(
                User.first_name.ilike(f'%{q}%'),
                User.last_name.ilike(f'%{q}%'),
                User.member_id.ilike(f'%{q}%'),
                Book.title.ilike(f'%{q}%'),
            )
        )

    borrows = query.order_by(Borrow.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config['BORROWS_PER_PAGE'],
        error_out=False
    )
    members = User.query.filter_by(role='member', is_active=True).order_by(User.first_name).all()

    return render_template('borrow/list.html',
                           borrows=borrows, status=status, q=q,
                           members=members, title='Borrow Records')


@borrow_bp.route('/my-borrows')
@login_required
def my_borrows():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    query = Borrow.query.filter_by(user_id=current_user.id)
    if status != 'all':
        query = query.filter_by(status=status)
    borrows = query.order_by(Borrow.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template('borrow/my_borrows.html',
                           borrows=borrows, status=status, title='My Borrows')


@borrow_bp.route('/overdue')
@login_required
@staff_required
def overdue_borrows():
    overdue = Borrow.query.filter(
        Borrow.status == 'borrowed',
        Borrow.due_date < date.today()
    ).order_by(Borrow.due_date.asc()).all()
    return render_template('borrow/overdue.html',
                           overdue=overdue, title='Overdue Books')


# ─── Fine Management ──────────────────────────────────────────────────────────

@borrow_bp.route('/fines')
@login_required
@staff_required
def all_fines():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    query = Fine.query
    if status != 'all':
        query = query.filter_by(status=status)
    fines = query.order_by(Fine.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('borrow/fines.html',
                           fines=fines, status=status, title='Fines')


@borrow_bp.route('/fines/<int:fine_id>/pay', methods=['POST'])
@login_required
@staff_required
def pay_fine(fine_id):
    fine = Fine.query.get_or_404(fine_id)
    method = request.form.get('payment_method', 'cash')
    fine.mark_paid(current_user.id, method)
    db.session.commit()
    flash(f'Fine of ${fine.amount_float:.2f} marked as paid. '
          f'Receipt: {fine.receipt_number}', 'success')
    return redirect(request.referrer or url_for('borrow.all_fines'))


@borrow_bp.route('/fines/<int:fine_id>/waive', methods=['POST'])
@login_required
def waive_fine(fine_id):
    if not current_user.is_admin:
        abort(403)
    fine = Fine.query.get_or_404(fine_id)
    reason = request.form.get('reason', '')
    fine.mark_waived(current_user.id, reason)
    db.session.commit()
    flash('Fine waived successfully.', 'success')
    return redirect(request.referrer or url_for('borrow.all_fines'))


# ─── AJAX: Search members ─────────────────────────────────────────────────────

@borrow_bp.route('/search-members')
@login_required
@staff_required
def search_members():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    members = User.query.filter(
        User.role == 'member',
        User.is_active == True,
        db.or_(
            User.first_name.ilike(f'%{q}%'),
            User.last_name.ilike(f'%{q}%'),
            User.member_id.ilike(f'%{q}%'),
            User.email.ilike(f'%{q}%'),
        )
    ).limit(10).all()
    return jsonify([{
        'id': m.id,
        'name': m.full_name,
        'member_id': m.member_id,
        'email': m.email,
        'active_borrows': m.active_borrows_count,
    } for m in members])
