"""
Comprehensive Test Suite for Kharcha Tracker
Tests:
- Multi-user authentication & session management
- 3 Security Questions password reset & verification
- Account deletion with cascade delete of data
- CRUD operations for Expenses, Grants, and Loans
- Mathematical correctness of Outflows, Inflows, Net Balance, and Loans
- Strict data isolation between multiple users
"""

import unittest
from datetime import date
from app import create_app, db
from app.models import User, Transaction

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    WTF_CSRF_ENABLED = False

class KharchaTrackerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_user(self, username, password, school='Beaconhouse', nickname='Mani', mother='Farhat'):
        return self.client.post('/auth/register', data={
            'username': username,
            'password': password,
            'confirm_password': password,
            'q1_school': school,
            'q2_nickname': nickname,
            'q3_mother': mother
        }, follow_redirects=True)

    def login_user(self, username, password):
        return self.client.post('/auth/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def logout_user(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_registration_and_login(self):
        """Test user registration and successful login"""
        response = self.register_user('umais', 'password123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome, umais', response.data)

        # Check DB
        user = User.query.filter_by(username='umais').first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('password123'))
        self.assertFalse(user.check_password('wrongpassword'))
        self.assertTrue(user.verify_security_answers('beaconhouse', 'mani', 'farhat'))

        # Logout and log back in
        self.logout_user()
        res_login = self.login_user('umais', 'password123')
        self.assertIn(b'Logged in successfully', res_login.data)

    def test_unauthenticated_access_redirects(self):
        """Unauthenticated requests to protected routes redirect to login"""
        res = self.client.get('/', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

    def test_password_reset_flow(self):
        """Test password reset using the 3 security questions"""
        self.register_user('friend1', 'secretPass', school='City School', nickname='Sunny', mother='Ayesha')
        self.logout_user()

        # Attempt reset with wrong answer
        res_fail = self.client.post('/auth/reset-password', data={
            'username': 'friend1',
            'q1_school': 'City School',
            'q2_nickname': 'WrongNick',
            'q3_mother': 'Ayesha',
            'new_password': 'newPassword123',
            'confirm_password': 'newPassword123'
        }, follow_redirects=True)
        self.assertIn(b'One or more security answers are incorrect', res_fail.data)

        # Attempt reset with correct answers (case-insensitive & trimmed)
        res_ok = self.client.post('/auth/reset-password', data={
            'username': 'friend1',
            'q1_school': '  city school ',
            'q2_nickname': 'sunny',
            'q3_mother': 'AYESHA',
            'new_password': 'newPassword123',
            'confirm_password': 'newPassword123'
        }, follow_redirects=True)
        self.assertIn(b'Your password has been reset successfully', res_ok.data)

        # Verify login with new password works
        res_login = self.login_user('friend1', 'newPassword123')
        self.assertIn(b'Logged in successfully', res_login.data)

    def test_crud_and_financial_arithmetic(self):
        """Test adding different transaction types and exact arithmetic computation"""
        self.register_user('finance_user', 'pass123')

        # 1. Add Expense: Food $100.50 (Paid)
        self.client.post('/expenses/add', data={
            'category': 'Food & Groceries',
            'amount': '100.50',
            'transaction_type': 'expense',
            'transaction_date': '2026-10-13',
            'note': 'Grocery shopping'
        }, follow_redirects=True)

        # 2. Add Grant/Income: Research Grant $1500.00 (Received)
        self.client.post('/expenses/add', data={
            'category': 'Grant / Stipend',
            'amount': '1500.00',
            'transaction_type': 'grant',
            'transaction_date': '2026-10-13',
            'note': 'Summer research grant'
        }, follow_redirects=True)

        # 3. Add Loan Given: Lent to Ali $300.00 (Paid)
        self.client.post('/expenses/add', data={
            'category': 'Personal Loan',
            'amount': '300.00',
            'transaction_type': 'loan_given',
            'transaction_date': '2026-10-13',
            'note': 'Lent to Ali'
        }, follow_redirects=True)

        # 4. Add Loan Taken: Borrowed from Uncle $200.00 (Received)
        self.client.post('/expenses/add', data={
            'category': 'Family Loan',
            'amount': '200.00',
            'transaction_type': 'loan_received',
            'transaction_date': '2026-10-13',
            'note': 'Emergency borrowed'
        }, follow_redirects=True)

        # Verify DB counts
        user = User.query.filter_by(username='finance_user').first()
        txs = Transaction.query.filter_by(user_id=user.id).all()
        self.assertEqual(len(txs), 4)

        # Arithmetic Verification:
        # Total Paid (Outflows) = 100.50 (expense) + 300.00 (loan_given) = 400.50
        # Total Received (Inflows) = 1500.00 (grant) + 200.00 (loan_received) = 1700.00
        # Net Balance = 1700.00 - 400.50 = 1299.50
        # Loans Given = 300.00
        # Loans Taken = 200.00
        total_paid = sum(tx.amount for tx in txs if tx.flow == 'paid')
        total_received = sum(tx.amount for tx in txs if tx.flow == 'received')
        net_balance = total_received - total_paid
        loans_given = sum(tx.amount for tx in txs if tx.transaction_type == 'loan_given')
        loans_received = sum(tx.amount for tx in txs if tx.transaction_type == 'loan_received')

        self.assertAlmostEqual(total_paid, 400.50, places=2)
        self.assertAlmostEqual(total_received, 1700.00, places=2)
        self.assertAlmostEqual(net_balance, 1299.50, places=2)
        self.assertAlmostEqual(loans_given, 300.00, places=2)
        self.assertAlmostEqual(loans_received, 200.00, places=2)

        # Check Dashboard render includes these values
        res_dash = self.client.get('/dashboard')
        self.assertIn(b'$1299.50', res_dash.data)
        self.assertIn(b'$400.50', res_dash.data)
        self.assertIn(b'$1700.00', res_dash.data)
        self.assertIn(b'$300.00', res_dash.data)
        self.assertIn(b'$200.00', res_dash.data)

        # Test Update / Edit
        tx_edit = Transaction.query.filter_by(category='Food & Groceries').first()
        self.client.post(f'/expenses/{tx_edit.id}/edit', data={
            'category': 'Food & Drinks',
            'amount': '150.00',
            'transaction_type': 'expense',
            'transaction_date': '2026-10-13',
            'note': 'Updated restaurant bill'
        }, follow_redirects=True)

        updated_tx = db.session.get(Transaction, tx_edit.id)
        self.assertEqual(updated_tx.category, 'Food & Drinks')
        self.assertEqual(updated_tx.amount, 150.00)

        # Test Delete
        self.client.post(f'/expenses/{tx_edit.id}/delete', follow_redirects=True)
        deleted_tx = db.session.get(Transaction, tx_edit.id)
        self.assertIsNone(deleted_tx)
        self.assertEqual(Transaction.query.filter_by(user_id=user.id).count(), 3)

    def test_multi_user_data_isolation(self):
        """User A and User B cannot see, modify, or delete each other's data"""
        # User A
        self.register_user('user_a', 'pass_a')
        self.client.post('/expenses/add', data={
            'category': 'Secret A Expense',
            'amount': '500.00',
            'transaction_type': 'expense',
            'transaction_date': '2026-10-13'
        }, follow_redirects=True)
        user_a = User.query.filter_by(username='user_a').first()
        tx_a = Transaction.query.filter_by(user_id=user_a.id).first()
        self.logout_user()

        # User B
        self.register_user('user_b', 'pass_b')
        self.client.post('/expenses/add', data={
            'category': 'Public B Expense',
            'amount': '75.00',
            'transaction_type': 'expense',
            'transaction_date': '2026-10-13'
        }, follow_redirects=True)

        # Check User B dashboard - User A's expense MUST NOT appear
        res_b = self.client.get('/dashboard')
        self.assertIn(b'Public B Expense', res_b.data)
        self.assertNotIn(b'Secret A Expense', res_b.data)

        # User B cannot edit User A's expense (should return 404)
        res_edit_attempt = self.client.post(f'/expenses/{tx_a.id}/edit', data={
            'category': 'Hacked',
            'amount': '1.00',
            'transaction_type': 'expense',
            'transaction_date': '2026-10-13'
        })
        self.assertEqual(res_edit_attempt.status_code, 404)

        # User B cannot delete User A's expense (should return 404)
        res_del_attempt = self.client.post(f'/expenses/{tx_a.id}/delete')
        self.assertEqual(res_del_attempt.status_code, 404)
        # Ensure tx_a is still intact in DB
        self.assertIsNotNone(db.session.get(Transaction, tx_a.id))

    def test_delete_account_cascade(self):
        """Deleting an account deletes the user and cascades to all their transactions"""
        self.register_user('delete_me', 'myPassword')
        user = User.query.filter_by(username='delete_me').first()
        
        # Add 2 transactions
        self.client.post('/expenses/add', data={
            'category': 'Item 1',
            'amount': '25.00',
            'transaction_type': 'expense',
            'transaction_date': '2026-10-13'
        })
        self.client.post('/expenses/add', data={
            'category': 'Item 2',
            'amount': '50.00',
            'transaction_type': 'grant',
            'transaction_date': '2026-10-13'
        })
        self.assertEqual(Transaction.query.filter_by(user_id=user.id).count(), 2)

        # Delete account with wrong password -> fails
        res_fail = self.client.post('/auth/delete-account', data={'password_confirm': 'wrong'}, follow_redirects=True)
        self.assertIn(b'Password verification failed', res_fail.data)
        self.assertIsNotNone(User.query.filter_by(username='delete_me').first())

        # Delete account with correct password -> succeeds
        res_ok = self.client.post('/auth/delete-account', data={'password_confirm': 'myPassword'}, follow_redirects=True)
        self.assertIn(b'permanently deleted', res_ok.data)

        # Verify user and transactions are completely removed
        self.assertIsNone(User.query.filter_by(username='delete_me').first())
        self.assertEqual(Transaction.query.filter_by(user_id=user.id).count(), 0)

if __name__ == '__main__':
    unittest.main()
