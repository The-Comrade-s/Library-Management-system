"""
tests/test_app.py - LibraTrack Test Suite
==========================================
Run with: pytest tests/ -v
Save at: LMS/tests/test_app.py
"""

import pytest
from app import create_app, db as _db
from app.models.user import User
from app.models.book import Book, Category
from app.models.borrow import Borrow


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope='session')
def app():
    """Create test application instance."""
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def db(app):
    with app.app_context():
        yield _db
        _db.session.rollback()


# ─── Auth Tests ───────────────────────────────────────────────────────────────

class TestAuth:
    def test_login_page_loads(self, client):
        res = client.get('/auth/login')
        assert res.status_code == 200
        assert b'Sign In' in res.data

    def test_register_page_loads(self, client):
        res = client.get('/auth/register')
        assert res.status_code == 200
        assert b'Create Account' in res.data

    def test_register_new_user(self, client):
        res = client.post('/auth/register', data={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'password': 'Test@1234',
            'confirm_password': 'Test@1234',
            'csrf_token': 'test'
        }, follow_redirects=True)
        # Should redirect to login after registration
        assert res.status_code == 200

    def test_login_invalid_credentials(self, client):
        res = client.post('/auth/login', data={
            'email': 'nobody@test.com',
            'password': 'wrongpassword',
            'csrf_token': 'test'
        }, follow_redirects=True)
        assert res.status_code == 200

    def test_logout_redirects(self, client):
        res = client.get('/auth/logout', follow_redirects=True)
        assert res.status_code == 200

    def test_protected_route_requires_login(self, client):
        res = client.get('/dashboard/admin', follow_redirects=True)
        assert res.status_code == 200
        assert b'Sign In' in res.data or b'log in' in res.data.lower()


# ─── Model Tests ─────────────────────────────────────────────────────────────

class TestUserModel:
    def test_generate_member_id(self, app):
        with app.app_context():
            mid = User.generate_member_id()
            assert mid.startswith('MEM-')

    def test_user_full_name(self, app):
        with app.app_context():
            u = User(first_name='Alice', last_name='Smith',
                     email='alice@test.com', password_hash='x',
                     member_id='MEM-TEST', role='member')
            assert u.full_name == 'Alice Smith'

    def test_user_role_properties(self, app):
        with app.app_context():
            admin = User(first_name='A', last_name='B', email='a@b.com',
                         password_hash='x', member_id='ADM-1', role='admin')
            assert admin.is_admin
            assert admin.can_manage
            assert not admin.is_member


class TestBookModel:
    def test_book_checkout_reduces_copies(self, app):
        with app.app_context():
            b = Book(title='Test', author='Author', total_copies=3, available_copies=3)
            b.checkout()
            assert b.available_copies == 2

    def test_book_checkin_restores_copies(self, app):
        with app.app_context():
            b = Book(title='Test2', author='Author', total_copies=3, available_copies=2)
            b.checkin()
            assert b.available_copies == 3

    def test_book_is_available(self, app):
        with app.app_context():
            b = Book(title='T', author='A', total_copies=1,
                     available_copies=1, is_active=True)
            assert b.is_available

    def test_book_not_available_when_zero_copies(self, app):
        with app.app_context():
            b = Book(title='T', author='A', total_copies=1,
                     available_copies=0, is_active=True)
            assert not b.is_available

    def test_barcode_generation(self, app):
        with app.app_context():
            b = Book(title='T', author='A', total_copies=1, available_copies=1)
            b.id = 42
            b.generate_barcode()
            assert b.barcode == 'LIB-000042'


# ─── Public Routes ────────────────────────────────────────────────────────────

class TestPublicRoutes:
    def test_home_page(self, client):
        res = client.get('/')
        assert res.status_code == 200

    def test_404_page(self, client):
        res = client.get('/nonexistent-route-xyz')
        assert res.status_code == 404


# ─── Config Tests ─────────────────────────────────────────────────────────────

class TestConfig:
    def test_testing_config(self, app):
        assert app.config['TESTING'] is True
        assert app.config['WTF_CSRF_ENABLED'] is False

    def test_fine_rate_default(self, app):
        assert app.config['DAILY_FINE_RATE'] == 0.50

    def test_borrow_duration_default(self, app):
        assert app.config['BORROW_DURATION_DAYS'] == 14
