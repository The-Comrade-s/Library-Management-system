"""
app/auth/forms.py - Authentication Forms
==========================================
WTForms with CSRF protection and server-side validation.
Save at: LMS/app/auth/forms.py
"""

from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SelectField,
                     SubmitField, DateField, TelField, TextAreaField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo,
                                Optional, Regexp, ValidationError)
from app.models.user import User


class LoginForm(FlaskForm):
    """Member / Staff login form."""
    email = StringField('Email Address', validators=[
        DataRequired(message='Email is required.'),
        Email(message='Enter a valid email address.')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """New member self-registration form."""
    first_name = StringField('First Name', validators=[
        DataRequired(), Length(min=2, max=50)
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(), Length(min=2, max=50)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(), Email(), Length(max=120)
    ])
    phone = TelField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters.'),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
            message='Password must contain uppercase, lowercase, and a number.'
        )
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Create Account')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('That email is already registered. Please log in.')


class ChangePasswordForm(FlaskForm):
    """Logged-in user password change."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
               message='Include uppercase, lowercase, and a number.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Update Password')


class EditProfileForm(FlaskForm):
    """User profile editing form."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    phone = TelField('Phone Number', validators=[Optional(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Changes')


class RequestPasswordResetForm(FlaskForm):
    """Request a password reset link via email."""
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    """Set new password after clicking reset link."""
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(min=8),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)',
               message='Include uppercase, lowercase, and a number.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')
