from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    # 3 Security Questions for Password Reset
    # Q1: Which school did you study last?
    # Q2: What is your nickname?
    # Q3: What is your mother's name?
    q1_school_hash = db.Column(db.String(256), nullable=False)
    q2_nickname_hash = db.Column(db.String(256), nullable=False)
    q3_mother_hash = db.Column(db.String(256), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # All related transactions are cascade deleted when user is deleted
    transactions = db.relationship('Transaction', backref='user', cascade='all, delete-orphan', lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def _normalize_answer(answer: str) -> str:
        return (answer or '').strip().lower()

    def set_security_answers(self, school: str, nickname: str, mother: str):
        self.q1_school_hash = generate_password_hash(self._normalize_answer(school))
        self.q2_nickname_hash = generate_password_hash(self._normalize_answer(nickname))
        self.q3_mother_hash = generate_password_hash(self._normalize_answer(mother))

    def verify_security_answers(self, school: str, nickname: str, mother: str) -> bool:
        v1 = check_password_hash(self.q1_school_hash, self._normalize_answer(school))
        v2 = check_password_hash(self.q2_nickname_hash, self._normalize_answer(nickname))
        v3 = check_password_hash(self.q3_mother_hash, self._normalize_answer(mother))
        return v1 and v2 and v3

    def __repr__(self):
        return f'<User {self.username}>'


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    # transaction_type: 'expense', 'grant', 'loan_given', 'loan_received'
    transaction_type = db.Column(db.String(20), nullable=False, default='expense')
    
    # flow: 'paid' (money goes out) or 'received' (money comes in)
    flow = db.Column(db.String(10), nullable=False, default='paid')
    
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def determine_flow(cls, transaction_type: str) -> str:
        """Determines whether transaction is an outflow ('paid') or inflow ('received')."""
        if transaction_type in ('expense', 'loan_given'):
            return 'paid'
        elif transaction_type in ('grant', 'loan_received'):
            return 'received'
        return 'paid'

    @property
    def badge_label(self) -> str:
        labels = {
            'expense': 'Expense (Paid)',
            'grant': 'Grant / Income (Received)',
            'loan_given': 'Loan Given (Paid Out)',
            'loan_received': 'Loan Taken (Received)',
        }
        return labels.get(self.transaction_type, self.transaction_type.title())

    @property
    def badge_class(self) -> str:
        classes = {
            'expense': 'badge-expense',
            'grant': 'badge-grant',
            'loan_given': 'badge-loan-given',
            'loan_received': 'badge-loan-received',
        }
        return classes.get(self.transaction_type, 'badge-default')

    def __repr__(self):
        return f'<Transaction {self.id}: {self.category} {self.amount} ({self.flow})>'
