"""
Legacy bridge for expense_track_project.
All persistent storage and business logic now use SQLAlchemy models (User, Transaction)
within the app/ module for multi-user security and relational integrity.
"""

from app.models import Transaction, User
from app import db

# Backwards compatibility alias
Expense = Transaction
