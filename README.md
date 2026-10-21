# 💰 Kharcha Tracker

A modern, multi-user personal expense, loan, and grant tracking web application built with **Flask**, **SQLAlchemy**, and a sleek **Glassmorphic Dark UI**.

Designed so that you and your friends can each have private, secure accounts with complete data isolation.

---

## ✨ Features

- **🔐 Simple & Private Multi-User Authentication**:
  - Username and password only (no OAuth or email required).
  - Strict user data isolation: each user can only see, create, edit, and delete their own financial records.
- **🛡️ 3-Question Password Reset**:
  - Secure account recovery powered by 3 personalized backup questions:
    1. *Which school did you study last?*
    2. *What is your nickname?*
    3. *What is your mother's name?*
  - Answers are normalized and cryptographically hashed for security.
- **🗑️ Account Deletion**:
  - Users can delete their account from settings with password confirmation.
  - Cascades and permanently wipes the account and all associated transactions.
- **📊 Comprehensive Financial Arithmetic**:
  - **Expense**: Outflows for everyday living (Food, Rent, Shopping, Bills).
  - **Grant / Income**: Inflows received (Stipends, Grants, Salary).
  - **Loan Given**: Outflow lent to friends/family (tracked as money owed to you).
  - **Loan Taken**: Inflow borrowed from someone (tracked as money you owe).
  - **Dynamic Dashboard Metrics**:
    - $\text{Net Balance} = \text{Total Received} - \text{Total Paid}$
    - $\text{Total Paid (Outflows)} = \text{Expenses} + \text{Loans Given}$
    - $\text{Total Received (Inflows)} = \text{Grants} + \text{Loans Taken}$
    - $\text{Active Loans Given}$ (pending return)
    - $\text{Active Loans Borrowed}$ (pending repayment)
- **⚡ Full CRUD Operations**:
  - Add, view, filter, edit, and delete records seamlessly.
  - Dynamic filtering by Type, Category, Month (`YYYY-MM`), and text search.
- **🎨 Glassmorphic Dark Design (`khobsorti.css`)**:
  - Built-in responsive dark UI with fiery orange/red accents, Poppins font, and responsive layout for mobile and desktop.
- **☁️ Deployment Ready**:
  - Runs with SQLite for zero-setup local development.
  - Ready for **Vercel** serverless deployment with `api/index.py` and `vercel.json` and supports hosted PostgreSQL (`DATABASE_URL`).

---

## 📁 Project Structure

```text
expense_tracker/
├── api/
│   └── index.py              # WSGI serverless entrypoint for Vercel
├── app/
│   ├── __init__.py           # Application Factory & extension initialization
│   ├── models.py             # User and Transaction SQLAlchemy models
│   ├── auth/                 # Authentication & Account Recovery Blueprint
│   │   ├── __init__.py
│   │   └── routes.py         # /login, /register, /reset-password, /logout, /delete-account
│   ├── expenses/             # Financial CRUD & Analytics Blueprint
│   │   ├── __init__.py
│   │   └── routes.py         # Full CRUD, dashboard metrics, filters
│   └── templates/
│       ├── base.html         # Navbar, flash messages, account deletion modal
│       ├── auth/
│       │   ├── login.html    # Login with forgot password link
│       │   ├── register.html # Registration with 3 security backup questions
│       │   └── reset_password.html # 3-question password reset
│       └── expenses/
│           ├── index.html    # Main dashboard with arithmetic cards & records table
│           ├── add.html      # Add transaction with type toggle & flow helper
│           └── edit.html     # Edit transaction
├── instance/                 # Local SQLite database (expenses.db)
├── static/
│   ├── css/
│   │   └── khobsorti.css     # Modern glassmorphic stylesheet
│   └── js/
│       └── expenses.js       # Client utilities & modal interactions
├── .env.example              # Environment variables template
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── run.py                    # Local runner script
├── test_app.py               # Automated unit & arithmetic test suite
└── vercel.json               # Vercel deployment configuration
```

---

##  Getting Started Locally

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python run.py
```
Or:
```bash
python kharcha_flask.py
```
Open your browser at `http://127.0.0.1:5000`.

### 3. Run the Automated Tests
```bash
python test_app.py
```
