"""
app/main/__init__.py - Main Blueprint
Save at: LMS/app/main/__init__.py
"""

from flask import Blueprint

main_bp = Blueprint('main', __name__)

from app.main import routes  # noqa: E402, F401
