"""
wsgi.py - WSGI Entry Point for Production
==========================================
Used by Gunicorn on Render: gunicorn wsgi:app
Save at: LMS/wsgi.py
"""

import os
from app import create_app

app = create_app('production')

if __name__ == '__main__':
    app.run()
