"""
app/auth/routes.py - Authentication Routes
Save at: LMS/app/auth/routes.py
"""

from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.auth.forms import (LoginForm, RegistrationForm, ChangePasswordForm,
                             EditProfileForm)
from app.models.user import User
from app import db, bcrypt


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Contact the library.', 'danger')
                return redirect(url_for('auth.login'))
            login_user(user, remember=form.remember_me.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.first_name}!', 'success')
            if next_page:
                return redirect(next_page)
            if user.can_manage:
                return redirect(url_for('dashboard.admin_dashboard'))
            return redirect(url_for('dashboard.member_dashboard'))
        flash('Invalid email or password. Please try again.', 'danger')
    return render_template('auth/login.html', form=form, title='Sign In')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            first_name=form.first_name.data.strip(),
            last_name=form.last_name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=form.phone.data,
            date_of_birth=form.date_of_birth.data,
            address=form.address.data,
            password_hash=hashed,
            role='member',
            is_active=True,
            member_id=User.generate_member_id(),
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, title='Register')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data.strip()
        current_user.last_name = form.last_name.data.strip()
        current_user.phone = form.phone.data
        current_user.date_of_birth = form.date_of_birth.data
        current_user.address = form.address.data
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))
    return render_template('auth/profile.html', form=form, title='My Profile')


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password_hash, form.current_password.data):
            current_user.password_hash = bcrypt.generate_password_hash(
                form.new_password.data).decode('utf-8')
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
        flash('Current password is incorrect.', 'danger')
    return render_template('auth/change_password.html', form=form, title='Change Password')
