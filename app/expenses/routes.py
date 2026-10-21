from datetime import datetime, date
import calendar
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.expenses import expenses_bp
from app.models import Transaction

DEFAULT_CATEGORIES = [
    'Food & Groceries',
    'Rent & Housing',
    'Utilities & Bills',
    'Transportation',
    'Healthcare & Medicine',
    'Education',
    'Entertainment',
    'Personal & Shopping',
    'Loan Repayment',
    'Grant / Stipend',
    'Miscellaneous'
]

@expenses_bp.route('/')
@expenses_bp.route('/dashboard')
@login_required
def dashboard():
    # Filter parameters
    filter_type = request.args.get('type', '').strip()
    filter_category = request.args.get('category', '').strip()
    filter_month = request.args.get('month', '').strip()  # format: YYYY-MM
    search_query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'date_desc').strip()

    # Base query strictly scoped to current user
    query = Transaction.query.filter_by(user_id=current_user.id)

    # Calculate overall arithmetic stats for the current user (unfiltered)
    all_user_txs = Transaction.query.filter_by(user_id=current_user.id).all()
    
    total_paid = sum(tx.amount for tx in all_user_txs if tx.flow == 'paid')
    total_received = sum(tx.amount for tx in all_user_txs if tx.flow == 'received')
    net_balance = total_received - total_paid

    expenses_total = sum(tx.amount for tx in all_user_txs if tx.transaction_type == 'expense')
    grants_total = sum(tx.amount for tx in all_user_txs if tx.transaction_type == 'grant')
    loans_given_total = sum(tx.amount for tx in all_user_txs if tx.transaction_type == 'loan_given')
    loans_received_total = sum(tx.amount for tx in all_user_txs if tx.transaction_type == 'loan_received')

    # Apply filters to table query
    if filter_type:
        query = query.filter(Transaction.transaction_type == filter_type)

    if filter_category:
        query = query.filter(Transaction.category == filter_category)

    if filter_month:
        try:
            year_str, month_str = filter_month.split('-')
            year, month = int(year_str), int(month_str)
            _, last_day = calendar.monthrange(year, month)
            start_date = date(year, month, 1)
            end_date = date(year, month, last_day)
            query = query.filter(Transaction.transaction_date >= start_date, Transaction.transaction_date <= end_date)
        except Exception:
            pass

    if search_query:
        query = query.filter(
            (Transaction.category.ilike(f'%{search_query}%')) |
            (Transaction.note.ilike(f'%{search_query}%'))
        )

    # Sorting
    if sort_by == 'date_asc':
        query = query.order_by(Transaction.transaction_date.asc(), Transaction.id.asc())
    elif sort_by == 'amount_desc':
        query = query.order_by(Transaction.amount.desc())
    elif sort_by == 'amount_asc':
        query = query.order_by(Transaction.amount.asc())
    else:  # default date_desc
        query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())

    transactions = query.all()

    # Filtered subset summary
    filtered_paid = sum(tx.amount for tx in transactions if tx.flow == 'paid')
    filtered_received = sum(tx.amount for tx in transactions if tx.flow == 'received')

    # Distinct categories for current user's dropdown
    user_categories = sorted(list({tx.category for tx in all_user_txs if tx.category}))
    available_categories = sorted(list(set(DEFAULT_CATEGORIES + user_categories)))

    return render_template(
        'expenses/index.html',
        transactions=transactions,
        total_paid=total_paid,
        total_received=total_received,
        net_balance=net_balance,
        expenses_total=expenses_total,
        grants_total=grants_total,
        loans_given_total=loans_given_total,
        loans_received_total=loans_received_total,
        filtered_paid=filtered_paid,
        filtered_received=filtered_received,
        available_categories=available_categories,
        filter_type=filter_type,
        filter_category=filter_category,
        filter_month=filter_month,
        search_query=search_query,
        sort_by=sort_by
    )


@expenses_bp.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        tx_type = request.form.get('transaction_type', 'expense').strip()
        date_raw = request.form.get('transaction_date', '').strip()
        note = request.form.get('note', '').strip()

        # Validation
        if not category:
            flash('Category is required.', 'danger')
            return render_template('expenses/add.html', available_categories=DEFAULT_CATEGORIES, today=date.today())

        try:
            amount = float(amount_raw)
            if amount <= 0:
                flash('Amount must be a positive number greater than zero.', 'danger')
                return render_template('expenses/add.html', available_categories=DEFAULT_CATEGORIES, today=date.today())
        except (ValueError, TypeError):
            flash('Please enter a valid numeric amount.', 'danger')
            return render_template('expenses/add.html', available_categories=DEFAULT_CATEGORIES, today=date.today())

        if tx_type not in ('expense', 'grant', 'loan_given', 'loan_received'):
            tx_type = 'expense'

        tx_date = date.today()
        if date_raw:
            try:
                tx_date = datetime.strptime(date_raw, '%Y-%m-%d').date()
            except ValueError:
                tx_date = date.today()

        flow = Transaction.determine_flow(tx_type)

        new_tx = Transaction(
            user_id=current_user.id,
            category=category,
            amount=amount,
            transaction_type=tx_type,
            flow=flow,
            transaction_date=tx_date,
            note=note
        )

        db.session.add(new_tx)
        db.session.commit()

        # Check if AJAX / JSON request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': True, 'id': new_tx.id, 'category': new_tx.category, 'amount': new_tx.amount}), 201

        flash(f'Transaction for "{category}" (${amount:,.2f}) added successfully!', 'success')
        return redirect(url_for('expenses.dashboard'))

    return render_template('expenses/add.html', available_categories=DEFAULT_CATEGORIES, today=date.today())


@expenses_bp.route('/expenses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
        category = request.form.get('category', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        tx_type = request.form.get('transaction_type', tx.transaction_type).strip()
        date_raw = request.form.get('transaction_date', '').strip()
        note = request.form.get('note', '').strip()

        if not category:
            flash('Category is required.', 'danger')
            return render_template('expenses/edit.html', tx=tx, available_categories=DEFAULT_CATEGORIES)

        try:
            amount = float(amount_raw)
            if amount <= 0:
                flash('Amount must be greater than zero.', 'danger')
                return render_template('expenses/edit.html', tx=tx, available_categories=DEFAULT_CATEGORIES)
        except (ValueError, TypeError):
            flash('Please enter a valid numeric amount.', 'danger')
            return render_template('expenses/edit.html', tx=tx, available_categories=DEFAULT_CATEGORIES)

        if tx_type not in ('expense', 'grant', 'loan_given', 'loan_received'):
            tx_type = 'expense'

        if date_raw:
            try:
                tx.transaction_date = datetime.strptime(date_raw, '%Y-%m-%d').date()
            except ValueError:
                pass

        tx.category = category
        tx.amount = amount
        tx.transaction_type = tx_type
        tx.flow = Transaction.determine_flow(tx_type)
        tx.note = note

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('expenses.dashboard'))

    return render_template('expenses/edit.html', tx=tx, available_categories=DEFAULT_CATEGORIES)


@expenses_bp.route('/expenses/<int:id>/delete', methods=['POST'])
@login_required
def delete_transaction(id):
    tx = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    cat = tx.category
    amt = tx.amount
    db.session.delete(tx)
    db.session.commit()
    flash(f'Transaction "{cat}" (${amt:,.2f}) deleted successfully.', 'info')
    return redirect(url_for('expenses.dashboard'))
