"""
app.py - Application Entry Point
==================================
Run locally: python app.py
Production:  gunicorn wsgi:app
Save at: LMS/app.py
"""

import os
from app import create_app

# Determine environment from FLASK_ENV variable
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = env == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
