"""
app/admin/routes.py - Admin User Management Routes
Save at: LMS/app/admin/routes.py
"""

from flask import (render_template, redirect, url_for, flash,
                   request, abort, current_app)
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, BooleanField, SubmitField, TelField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, Regexp
from app.admin import admin_bp
from app.models.user import User
from app.models.borrow import Borrow
from app.models.fine import Fine
from app import db, bcrypt


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_manage:
            abort(403)
        return f(*args, **kwargs)
    return decorated


class CreateUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = TelField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    role = SelectField('Role', choices=[
        ('member', 'Member'), ('librarian', 'Librarian'), ('admin', 'Admin')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=8),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
               message='Must include upper, lower, and number.')
    ])
    confirm = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password')
    ])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Create User')

    def validate_email(self, field):
        from wtforms.validators import ValidationError
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered.')


class EditUserForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone = TelField('Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional()])
    role = SelectField('Role', choices=[
        ('member', 'Member'), ('librarian', 'Librarian'), ('admin', 'Admin')
    ])
    is_active = BooleanField('Active')
    submit = SubmitField('Save Changes')


# ─── User List ────────────────────────────────────────────────────────────────

@admin_bp.route('/users')
@login_required
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '').strip()
    role = request.args.get('role', 'all')

    query = User.query
    if q:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{q}%'),
                User.last_name.ilike(f'%{q}%'),
                User.email.ilike(f'%{q}%'),
                User.member_id.ilike(f'%{q}%'),
            )
        )
    if role != 'all':
        query = query.filter_by(role=role)

    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config['USERS_PER_PAGE'], error_out=False
    )
    return render_template('admin/users.html',
                           users=users, q=q, role=role, title='User Management')


@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    borrows = Borrow.query.filter_by(user_id=user_id).order_by(
        Borrow.created_at.desc()).limit(20).all()
    fines = Fine.query.filter_by(user_id=user_id).order_by(
        Fine.created_at.desc()).all()
    return render_template('admin/user_detail.html',
                           user=user, borrows=borrows, fines=fines,
                           title=user.full_name)


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data,
            address=form.address.data,
            role=form.role.data,
            is_active=form.is_active.data,
            password_hash=bcrypt.generate_password_hash(
                form.password.data).decode('utf-8'),
            member_id=User.generate_member_id(),
        )
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.full_name} created ({user.member_id}).', 'success')
        return redirect(url_for('admin.user_list'))
    return render_template('admin/user_form.html', form=form,
                           title='Create User', action='create')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        user.first_name = form.first_name.data.strip()
        user.last_name = form.last_name.data.strip()
        user.phone = form.phone.data
        user.address = form.address.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        db.session.commit()
        flash('User updated.', 'success')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    return render_template('admin/user_form.html', form=form, user=user,
                           title='Edit User', action='edit')


@admin_bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.user_list'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'{user.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.user_list'))


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password', '').strip()
    if len(new_password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
    db.session.commit()
    flash(f'Password for {user.full_name} has been reset.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.user_list'))
    if user.borrows.filter_by(status='borrowed').count() > 0:
        flash('Cannot delete: user has active borrows.', 'danger')
        return redirect(url_for('admin.user_detail', user_id=user_id))
    name = user.full_name
    db.session.delete(user)
    db.session.commit()
    flash(f'User {name} deleted.', 'success')
    return redirect(url_for('admin.user_list'))
