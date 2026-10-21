from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.auth import auth_bp
from app.models import User

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('expenses.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        q1_school = request.form.get('q1_school', '').strip()
        q2_nickname = request.form.get('q2_nickname', '').strip()
        q3_mother = request.form.get('q3_mother', '').strip()

        # Validations
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters long.', 'danger')
            return render_template('auth/register.html', username=username)

        if not password or len(password) < 4:
            flash('Password must be at least 4 characters long.', 'danger')
            return render_template('auth/register.html', username=username)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', username=username)

        if not (q1_school and q2_nickname and q3_mother):
            flash('All 3 security questions must be answered for account recovery.', 'danger')
            return render_template('auth/register.html', username=username)

        existing_user = User.query.filter(User.username.ilike(username)).first()
        if existing_user:
            flash('Username is already taken. Please choose another one.', 'warning')
            return render_template('auth/register.html', username=username)

        # Create user
        user = User(username=username)
        user.set_password(password)
        user.set_security_answers(q1_school, q2_nickname, q3_mother)

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f'Welcome, {user.username}! Your account has been registered.', 'success')
        return redirect(url_for('expenses.dashboard'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('expenses.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please provide both username and password.', 'danger')
            return render_template('auth/login.html', username=username)

        user = User.query.filter(User.username.ilike(username)).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('auth/login.html', username=username)

        login_user(user, remember=True)
        flash(f'Logged in successfully as {user.username}.', 'success')
        
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('expenses.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('expenses.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        q1_school = request.form.get('q1_school', '').strip()
        q2_nickname = request.form.get('q2_nickname', '').strip()
        q3_mother = request.form.get('q3_mother', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not (username and q1_school and q2_nickname and q3_mother and new_password):
            flash('All fields are required to reset your password.', 'danger')
            return render_template('auth/reset_password.html', username=username)

        if len(new_password) < 4:
            flash('New password must be at least 4 characters long.', 'danger')
            return render_template('auth/reset_password.html', username=username)

        if new_password != confirm_password:
            flash('New passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', username=username)

        user = User.query.filter(User.username.ilike(username)).first()
        if not user:
            flash('User with that username does not exist.', 'danger')
            return render_template('auth/reset_password.html', username=username)

        if not user.verify_security_answers(q1_school, q2_nickname, q3_mother):
            flash('One or more security answers are incorrect. Verification failed.', 'danger')
            return render_template('auth/reset_password.html', username=username)

        # Update password
        user.set_password(new_password)
        db.session.commit()

        flash('Your password has been reset successfully! You can now log in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    password_confirm = request.form.get('password_confirm', '')
    user_id = current_user.id
    user = db.get_or_404(User, user_id)

    if not user.check_password(password_confirm):
        flash('Password verification failed. Account was NOT deleted.', 'danger')
        return redirect(url_for('expenses.dashboard'))

    username = user.username
    logout_user()
    db.session.delete(user)
    db.session.commit()

    flash(f'Account "{username}" and all related expenses have been permanently deleted.', 'info')
    return redirect(url_for('auth.register'))
