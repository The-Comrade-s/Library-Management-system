"""
app/books/routes.py - Book Management Routes
Save at: LMS/app/books/routes.py
"""

import os
import uuid
from flask import (render_template, redirect, url_for, flash,
                   request, current_app, abort)
from flask_login import login_required, current_user
from app.books import books_bp
from app.books.forms import BookForm, CategoryForm, BookSearchForm
from app.models.book import Book, Category
from app import db
from PIL import Image


def staff_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def save_cover_image(file_obj):
    """Resize and save uploaded cover image. Returns filename."""
    ext = file_obj.filename.rsplit('.', 1)[-1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    covers_dir = os.path.join(current_app.root_path, 'static', 'images', 'covers')
    os.makedirs(covers_dir, exist_ok=True)
    path = os.path.join(covers_dir, filename)

    try:
        img = Image.open(file_obj)
        img.thumbnail((400, 600))
        img.save(path, optimize=True, quality=85)
    except Exception:
        file_obj.seek(0)
        file_obj.save(path)

    return filename


# ─── Book Listing & Search ────────────────────────────────────────────────────

@books_bp.route('/')
@login_required
def list_books():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    cat_id = request.args.get('category', 0, type=int)
    avail = request.args.get('availability', 0, type=int)

    query = Book.query.filter_by(is_active=True)

    if q:
        like = f'%{q}%'
        query = query.filter(
            db.or_(
                Book.title.ilike(like),
                Book.author.ilike(like),
                Book.isbn.ilike(like),
                Book.publisher.ilike(like),
            )
        )
    if cat_id:
        query = query.filter_by(category_id=cat_id)
    if avail == 1:
        query = query.filter(Book.available_copies > 0)
    elif avail == 2:
        query = query.filter(Book.available_copies == 0)

    books = query.order_by(Book.title).paginate(
        page=page, per_page=current_app.config['BOOKS_PER_PAGE'], error_out=False
    )
    categories = Category.query.order_by(Category.name).all()
    form = BookSearchForm()

    return render_template('books/list.html',
                           books=books, categories=categories,
                           form=form, q=q, cat_id=cat_id, avail=avail,
                           title='Books')


@books_bp.route('/<int:book_id>')
@login_required
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    from app.models.borrow import Borrow
    borrow_history = book.borrows.order_by(Borrow.borrow_date.desc()).limit(10).all()
    user_has_borrowed = False
    if current_user.is_member:
        user_has_borrowed = book.borrows.filter_by(
            user_id=current_user.id, status='borrowed'
        ).first() is not None
    return render_template('books/detail.html', book=book,
                           borrow_history=borrow_history,
                           user_has_borrowed=user_has_borrowed,
                           title=book.title)


# ─── Add Book ─────────────────────────────────────────────────────────────────

@books_bp.route('/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        cover_filename = None
        if form.cover_image.data:
            cover_filename = save_cover_image(form.cover_image.data)

        book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            isbn=form.isbn.data.strip() or None,
            publisher=form.publisher.data.strip() or None,
            publication_year=form.publication_year.data,
            edition=form.edition.data.strip() or None,
            language=form.language.data.strip() or 'English',
            pages=form.pages.data,
            description=form.description.data,
            category_id=form.category_id.data or None,
            barcode=form.barcode.data.strip() or None,
            shelf_location=form.shelf_location.data.strip() or None,
            total_copies=form.total_copies.data,
            available_copies=form.total_copies.data,
            cover_image=cover_filename,
            is_active=form.is_active.data,
        )
        db.session.add(book)
        db.session.flush()
        book.generate_barcode()
        db.session.commit()
        flash(f'Book "{book.title}" added successfully.', 'success')
        return redirect(url_for('books.book_detail', book_id=book.id))

    return render_template('books/form.html', form=form,
                           title='Add New Book', action='add')


# ─── Edit Book ────────────────────────────────────────────────────────────────

@books_bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm(obj=book)

    if form.validate_on_submit():
        if form.cover_image.data:
            # Delete old cover
            if book.cover_image and book.cover_image != 'default_cover.jpg':
                old_path = os.path.join(
                    current_app.root_path, 'static', 'images', 'covers', book.cover_image
                )
                if os.path.exists(old_path):
                    os.remove(old_path)
            book.cover_image = save_cover_image(form.cover_image.data)

        copies_diff = form.total_copies.data - book.total_copies
        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.isbn = form.isbn.data.strip() or None
        book.publisher = form.publisher.data.strip() or None
        book.publication_year = form.publication_year.data
        book.edition = form.edition.data.strip() or None
        book.language = form.language.data.strip() or 'English'
        book.pages = form.pages.data
        book.description = form.description.data
        book.category_id = form.category_id.data or None
        book.barcode = form.barcode.data.strip() or None
        book.shelf_location = form.shelf_location.data.strip() or None
        book.total_copies = form.total_copies.data
        book.available_copies = max(0, book.available_copies + copies_diff)
        book.is_active = form.is_active.data

        db.session.commit()
        flash(f'Book "{book.title}" updated.', 'success')
        return redirect(url_for('books.book_detail', book_id=book.id))

    return render_template('books/form.html', form=form, book=book,
                           title='Edit Book', action='edit')


# ─── Delete Book ──────────────────────────────────────────────────────────────

@books_bp.route('/<int:book_id>/delete', methods=['POST'])
@login_required
@staff_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.borrows.filter_by(status='borrowed').count() > 0:
        flash('Cannot delete: this book has active borrows.', 'danger')
        return redirect(url_for('books.book_detail', book_id=book_id))
    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{title}" deleted.', 'success')
    return redirect(url_for('books.list_books'))


# ─── Categories ───────────────────────────────────────────────────────────────

@books_bp.route('/categories')
@login_required
def list_categories():
    categories = Category.query.order_by(Category.name).all()
    return render_template('books/categories.html',
                           categories=categories, title='Categories')


@books_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@staff_required
def add_category():
    form = CategoryForm()
    if form.validate_on_submit():
        cat = Category(name=form.name.data.strip(), description=form.description.data)
        db.session.add(cat)
        db.session.commit()
        flash(f'Category "{cat.name}" created.', 'success')
        return redirect(url_for('books.list_categories'))
    return render_template('books/category_form.html', form=form, title='Add Category')


@books_bp.route('/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def edit_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        cat.name = form.name.data.strip()
        cat.description = form.description.data
        db.session.commit()
        flash('Category updated.', 'success')
        return redirect(url_for('books.list_categories'))
    return render_template('books/category_form.html', form=form,
                           cat=cat, title='Edit Category')


@books_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@staff_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.books.count() > 0:
        flash('Cannot delete: category has books assigned.', 'danger')
        return redirect(url_for('books.list_categories'))
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'success')
    return redirect(url_for('books.list_categories'))
