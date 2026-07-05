import os
from app import create_app, db

app = create_app('production')

with app.app_context():
    try:
        db.create_all()
        print("Tables created successfully")
    except Exception as e:
        print(f"DB init error: {e}")

if __name__ == '__main__':
    app.run()
