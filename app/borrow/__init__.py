"""app/borrow/__init__.py"""
from flask import Blueprint
borrow_bp = Blueprint('borrow', __name__)
from app.borrow import routes  # noqa
