import os
from app import create_app, db
from app.models.user import User
from app.models.book import Category
from app import bcrypt

app = create_app('production')

with app.app_context():
    try:
        db.create_all()
        print("Tables created successfully")
        
        # Create admin if not exists
        if not User.query.filter_by(email='admin@library.com').first():
            admin = User(
                first_name='System',
                last_name='Administrator',
                email='admin@library.com',
                password_hash=bcrypt.generate_password_hash('Admin@123456').decode('utf-8'),
                role='admin',
                is_active=True,
                member_id='ADM-0001',
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin account created")
        else:
            print("Admin already exists")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    app.run()
