"""
app/dashboard/__init__.py
Save at: LMS/app/dashboard/__init__.py
"""
from flask import Blueprint
dashboard_bp = Blueprint('dashboard', __name__)
from app.dashboard import routes  # noqa
