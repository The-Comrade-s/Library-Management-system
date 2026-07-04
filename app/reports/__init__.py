"""app/reports/__init__.py"""
from flask import Blueprint
reports_bp = Blueprint('reports', __name__)
from app.reports import routes  # noqa
