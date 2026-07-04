# LibraTrack – Library Management System

> A complete, production-ready Library Management System built with Python/Flask, PostgreSQL, and Bootstrap 5. Final-year Computer Science project.

**Live Demo:** `https://libratrack.onrender.com` *(replace with your actual URL after deployment)*

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Quick Start – Local](#quick-start--local)
4. [GitHub Setup](#github-setup)
5. [Render Deployment](#render-deployment)
6. [Default Credentials](#default-credentials)
7. [Testing Checklist](#testing-checklist)
8. [Folder Structure](#folder-structure)
9. [API & Routes Reference](#api--routes-reference)
10. [Database Schema](#database-schema)
11. [Common Errors & Fixes](#common-errors--fixes)

---

## Features

| Module | Features |
|--------|----------|
| **Authentication** | Register, login, logout, profile, change password, role-based access |
| **Books** | Add/edit/delete books, cover upload, ISBN/barcode, search, pagination |
| **Categories** | Create/edit/delete categories, assign to books |
| **Borrow System** | Issue books, return books, due-date tracking, member limits |
| **Overdue** | Auto-detect overdue, daily fine calculation ($0.50/day) |
| **Fines** | Pay fines (cash/card/online), waive fines, generate receipts |
| **Admin** | User management, activate/deactivate, reset passwords |
| **Reports** | Borrowed, overdue, popular books, active members, fines summary, CSV export |
| **Dashboard** | Admin stats + charts, member personal dashboard |

---

## Tech Stack

- **Backend:** Python 3.11, Flask 3.0, Flask-SQLAlchemy, Flask-Login, Flask-Migrate, Flask-Bcrypt, Flask-WTF
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Frontend:** Bootstrap 5, Chart.js, Bootstrap Icons
- **Deployment:** Render (web service + PostgreSQL)
- **Security:** CSRF protection, password hashing (bcrypt), SQL injection protection via ORM

---

## Quick Start – Local

### Prerequisites
- Python 3.10+
- Git
- (Optional) PostgreSQL for local DB testing

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/libratrack.git
cd libratrack

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env
# Edit .env with your settings (SQLite is used by default locally)

# 5. Run the app
python app.py
```

Open http://localhost:5000 in your browser.

**Default Admin Login:**
- Email: `admin@library.com`
- Password: `Admin@123456`

---

## GitHub Setup

```bash
# Initialize repo (first time only)
git init
git add .
git commit -m "Initial commit: Complete LibraTrack LMS"

# Create a new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/libratrack.git
git branch -M main
git push -u origin main
```

---

## Render Deployment

### Step 1 – Create a PostgreSQL Database on Render
1. Go to https://render.com and sign in
2. Click **New** → **PostgreSQL**
3. Name: `libratrack-db`
4. Plan: **Free**
5. Region: **Oregon (US West)**
6. Click **Create Database**
7. Copy the **External Database URL** — you'll need it

### Step 2 – Create the Web Service
1. Click **New** → **Web Service**
2. Connect your GitHub repository
3. Settings:
   - **Name:** `libratrack`
   - **Region:** Oregon
   - **Branch:** `main`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120`
   - **Plan:** Free

### Step 3 – Set Environment Variables
In your Render web service → **Environment** tab, add:

| Key | Value |
|-----|-------|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | *(click Generate)* |
| `DATABASE_URL` | *(paste your PostgreSQL External URL)* |
| `DAILY_FINE_RATE` | `0.50` |
| `BORROW_DURATION_DAYS` | `14` |
| `ADMIN_EMAIL` | `admin@library.com` |
| `ADMIN_PASSWORD` | `Admin@123456` |

### Step 4 – Deploy
1. Click **Create Web Service**
2. Wait ~3–5 minutes for the build
3. Your app is live at: `https://libratrack.onrender.com`
4. The database tables and admin account are created automatically on first boot

### Step 5 – Verify Deployment
1. Visit your public URL
2. Log in with `admin@library.com` / `Admin@123456`
3. Go to Admin → Add some books and users
4. Test borrowing and returning

---

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@library.com | Admin@123456 |

To create member accounts, go to Admin → Users → Add User, or use the public Register page.

---

## Testing Checklist

### Authentication
- [ ] Register a new member account
- [ ] Log in with the new account
- [ ] Log in with admin credentials
- [ ] Log out and verify session is cleared
- [ ] Try accessing `/dashboard/admin` without login → should redirect to login
- [ ] Try accessing `/admin/users` as a member → should show 403

### Books
- [ ] Add a new book with all fields and a cover image
- [ ] Search books by title, author, ISBN
- [ ] Filter books by category
- [ ] Filter books by availability
- [ ] Edit a book
- [ ] Delete a book that has no active borrows
- [ ] Verify barcode auto-generated as `LIB-XXXXXX`

### Borrow System
- [ ] Issue a book to a member (as admin/librarian)
- [ ] Verify available copies decrease by 1
- [ ] Return the book
- [ ] Verify available copies restore
- [ ] Try to issue to a member who already has 5 books → blocked
- [ ] Members can self-borrow from book detail page

### Overdue & Fines
- [ ] Change a borrow's due_date to yesterday in DB to simulate overdue
- [ ] Return overdue book → fine automatically created
- [ ] Pay a fine → receipt number generated
- [ ] Waive a fine (admin only)
- [ ] Export overdue list as CSV

### Reports
- [ ] View Borrowed Books report
- [ ] View Overdue report
- [ ] View Popular Books report
- [ ] View Active Members report
- [ ] View Fines Summary report
- [ ] View Inventory report
- [ ] Export overdue CSV

### Admin
- [ ] Create a librarian account
- [ ] Deactivate a member account
- [ ] Activate the account again
- [ ] Reset a user's password
- [ ] Add a new book category
- [ ] Delete an empty category

### Dashboard
- [ ] Admin dashboard shows correct stats
- [ ] Charts render (monthly borrows, category distribution)
- [ ] Overdue alert section shows red entries
- [ ] Member dashboard shows active borrows and fines

---

## Folder Structure

```
Library-Management-System/
├── app/
│   ├── __init__.py          # App factory
│   ├── auth/                # Authentication blueprint
│   ├── books/               # Book management blueprint
│   ├── borrow/              # Borrow/return/fines blueprint
│   ├── dashboard/           # Dashboard blueprint
│   ├── admin/               # Admin user management blueprint
│   ├── reports/             # Reports blueprint
│   ├── main/                # Public landing page blueprint
│   ├── models/              # SQLAlchemy models
│   │   ├── user.py
│   │   ├── book.py
│   │   ├── borrow.py
│   │   └── fine.py
│   ├── templates/           # Jinja2 HTML templates
│   └── static/              # CSS, JS, images
│       ├── css/style.css
│       ├── js/main.js
│       └── images/covers/
├── tests/
│   └── test_app.py
├── migrations/
├── app.py                   # Dev entry point
├── wsgi.py                  # Production entry point
├── config.py                # Configuration classes
├── requirements.txt
├── render.yaml              # Render deployment config
├── Procfile
├── .env.example
└── README.md
```

---

## API & Routes Reference

| Method | Route | Access | Description |
|--------|-------|--------|-------------|
| GET | `/` | Public | Landing page |
| GET/POST | `/auth/login` | Public | Login |
| GET/POST | `/auth/register` | Public | Register |
| GET | `/auth/logout` | Auth | Logout |
| GET/POST | `/auth/profile` | Auth | View/edit profile |
| GET | `/dashboard/admin` | Staff | Admin dashboard |
| GET | `/dashboard/member` | Member | Member dashboard |
| GET | `/books/` | Auth | Book list/search |
| GET | `/books/<id>` | Auth | Book detail |
| GET/POST | `/books/add` | Staff | Add book |
| GET/POST | `/books/<id>/edit` | Staff | Edit book |
| POST | `/books/<id>/delete` | Staff | Delete book |
| GET | `/books/categories` | Auth | List categories |
| POST | `/borrow/issue/<book_id>` | Staff | Issue book to member |
| POST | `/borrow/self-borrow/<book_id>` | Member | Self-borrow |
| POST | `/borrow/return/<id>` | Staff | Return book |
| GET | `/borrow/` | Staff | All borrow records |
| GET | `/borrow/my-borrows` | Member | My borrows |
| GET | `/borrow/overdue` | Staff | Overdue list |
| GET | `/borrow/fines` | Staff | Fines management |
| POST | `/borrow/fines/<id>/pay` | Staff | Mark fine paid |
| POST | `/borrow/fines/<id>/waive` | Admin | Waive fine |
| GET | `/admin/users` | Staff | User list |
| GET/POST | `/admin/users/create` | Staff | Create user |
| GET/POST | `/admin/users/<id>/edit` | Staff | Edit user |
| POST | `/admin/users/<id>/delete` | Admin | Delete user |
| GET | `/reports/` | Staff | Reports index |
| GET | `/reports/overdue` | Staff | Overdue report |
| GET | `/reports/export/overdue-csv` | Staff | CSV export |

---

## Database Schema

```
users
  id, member_id, first_name, last_name, email, phone, address
  password_hash, role (admin/librarian/member), is_active
  created_at, updated_at, last_login

categories
  id, name, description, created_at

books
  id, title, author, isbn, publisher, publication_year, edition
  language, pages, description, category_id (FK), barcode
  shelf_location, total_copies, available_copies
  cover_image, is_active, created_at, updated_at

borrows
  id, user_id (FK), book_id (FK), issued_by (FK)
  borrow_date, due_date, return_date
  status (borrowed/returned/overdue), notes
  created_at, updated_at

fines
  id, borrow_id (FK), user_id (FK)
  amount, days_overdue, daily_rate
  status (unpaid/paid/waived)
  paid_at, paid_by (FK), payment_method, receipt_number
  created_at, updated_at
```

**Relationships:**
- User → Borrows: One-to-Many
- User → Fines: One-to-Many
- Book → Borrows: One-to-Many
- Category → Books: One-to-Many
- Borrow → Fine: One-to-One

---

## Common Errors & Fixes

### App won't start locally
```
Error: No module named 'flask'
Fix: Activate virtual environment: source venv/bin/activate
     Then: pip install -r requirements.txt
```

### Database error on startup
```
Error: FATAL: database does not exist
Fix: Check DATABASE_URL in .env matches your PostgreSQL setup
     For local dev, use: DATABASE_URL=sqlite:///library_dev.db
```

### Render deployment fails
```
Error: Build failed
Fix 1: Check requirements.txt has all dependencies
Fix 2: Ensure Python version ≥ 3.10 (set in Render settings)
Fix 3: Check build logs for specific error
```

### Images not showing
```
Problem: Book covers show placeholder
Fix: The covers directory needs write permissions
     On Render, uploaded images don't persist between deploys
     Use cloud storage (Cloudinary) for production cover images
```

### CSRF token missing
```
Error: 400 Bad Request / CSRF token missing
Fix: Ensure all POST forms include: <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

### 503 on Render (free tier)
```
Problem: App sleeps after 15 minutes of inactivity
Fix: This is normal on the free tier. First request after sleep takes ~30 seconds.
     Upgrade to paid plan to avoid sleep.
```

---

## Git Commands for Each Milestone

```bash
# After setting up project
git add . && git commit -m "feat: Initial project setup with app factory"

# After models
git add . && git commit -m "feat: Add SQLAlchemy models (User, Book, Borrow, Fine)"

# After auth
git add . && git commit -m "feat: Complete authentication module"

# After books
git add . && git commit -m "feat: Complete book management module"

# After borrow system
git add . && git commit -m "feat: Complete borrow/return/fines system"

# After templates
git add . && git commit -m "feat: Complete all HTML templates"

# After deployment
git add . && git commit -m "deploy: Configure Render deployment"

git push origin main
```

---

## License

MIT License – Free to use for academic and educational purposes.

---

*Built with ❤️ using Flask, PostgreSQL, and Bootstrap 5*
