# Additional routes for the expense tracker application

from app import app, get_db_connection, login_required, session
from flask import jsonify, request
from datetime import datetime, timedelta
import calendar

@app.route('/api/transactions')
@login_required
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT t.id, t.amount, t.type, t.transaction_date, t.description,
               c.name as category_name, a.name as account_name, 
               a2.name as to_account_name
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts a ON t.account_id = a.id
        LEFT JOIN accounts a2 ON t.to_account_id = a2.id
        WHERE t.user_id = %s
        ORDER BY t.transaction_date DESC, t.created_at DESC
        LIMIT 50
    """, (session['user_id'],))
    
    transactions = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{
        'id': t[0],
        'amount': float(t[1]),
        'type': t[2],
        'transaction_date': t[3].isoformat() if t[3] else None,
        'description': t[4],
        'category_name': t[5],
        'account_name': t[6],
        'to_account_name': t[7]
    } for t in transactions])

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get transaction details first
        cursor.execute("""
            SELECT account_id, to_account_id, amount, type 
            FROM transactions 
            WHERE id = %s AND user_id = %s
        """, (transaction_id, session['user_id']))
        
        transaction = cursor.fetchone()
        if not transaction:
            return jsonify({'success': False, 'error': 'Transaction not found'})
        
        account_id, to_account_id, amount, trans_type = transaction
        
        # Reverse the account balance changes
        if trans_type == 'income':
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, account_id))
        elif trans_type == 'expense':
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account_id))
        elif trans_type == 'transfer':
            cursor.execute("UPDATE accounts SET balance = balance + %s WHERE id = %s", (amount, account_id))
            cursor.execute("UPDATE accounts SET balance = balance - %s WHERE id = %s", (amount, to_account_id))
        
        # Delete the transaction
        cursor.execute("DELETE FROM transactions WHERE id = %s AND user_id = %s", (transaction_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/analysis/<analysis_type>')
@login_required
def get_analysis_data(analysis_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    if analysis_type == 'expense_overview':
        cursor.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s AND t.type = 'expense'
            AND MONTH(t.transaction_date) = %s AND YEAR(t.transaction_date) = %s
            GROUP BY c.id, c.name
            ORDER BY total DESC
        """, (session['user_id'], current_month, current_year))
        
    elif analysis_type == 'income_overview':
        cursor.execute("""
            SELECT c.name, SUM(t.amount) as total
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = %s AND t.type = 'income'
            AND MONTH(t.transaction_date) = %s AND YEAR(t.transaction_date) = %s
            GROUP BY c.id, c.name
            ORDER BY total DESC
        """, (session['user_id'], current_month, current_year))
        
    elif analysis_type == 'expense_flow':
        # Get last 6 months of expense data
        cursor.execute("""
            SELECT MONTH(t.transaction_date) as month, YEAR(t.transaction_date) as year, SUM(t.amount) as total
            FROM transactions t
            WHERE t.user_id = %s AND t.type = 'expense'
            AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY YEAR(t.transaction_date), MONTH(t.transaction_date)
            ORDER BY year, month
        """, (session['user_id'],))
        
    elif analysis_type == 'income_flow':
        # Get last 6 months of income data
        cursor.execute("""
            SELECT MONTH(t.transaction_date) as month, YEAR(t.transaction_date) as year, SUM(t.amount) as total
            FROM transactions t
            WHERE t.user_id = %s AND t.type = 'income'
            AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY YEAR(t.transaction_date), MONTH(t.transaction_date)
            ORDER BY year, month
        """, (session['user_id'],))
    
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if analysis_type in ['expense_overview', 'income_overview']:
        return jsonify({
            'labels': [row[0] for row in data],
            'values': [float(row[1]) for row in data]
        })
    else:
        # For flow charts, format month names
        labels = []
        values = []
        for row in data:
            month_name = calendar.month_abbr[row[0]]
            year = row[1]
            labels.append(f"{month_name} {year}")
            values.append(float(row[2]))
        
        return jsonify({
            'labels': labels,
            'values': values
        })

@app.route('/api/budgets')
@login_required
def get_budgets():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    cursor.execute("""
        SELECT b.category_id, b.amount, c.name,
               COALESCE(SUM(t.amount), 0) as spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        LEFT JOIN transactions t ON t.category_id = b.category_id 
            AND t.type = 'expense' 
            AND MONTH(t.transaction_date) = b.month 
            AND YEAR(t.transaction_date) = b.year
            AND t.user_id = %s
        WHERE b.user_id = %s AND b.month = %s AND b.year = %s
        GROUP BY b.category_id, b.amount, c.name
    """, (session['user_id'], session['user_id'], current_month, current_year))
    
    budgets = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify([{
        'category_id': budget[0],
        'amount': float(budget[1]),
        'category_name': budget[2],
        'spent': float(budget[3])
    } for budget in budgets])

@app.route('/api/budgets', methods=['POST'])
@login_required
def set_budget():
    data = request.json
    category_id = data['category_id']
    amount = data['amount']
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO budgets (user_id, category_id, amount, month, year)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE amount = %s
        """, (session['user_id'], category_id, amount, current_month, current_year, amount))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts', methods=['POST'])
@login_required
def add_account():
    data = request.json
    name = data['name']
    initial_amount = data.get('initial_amount', 0)
    account_type = data.get('account_type', 'personal')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO accounts (user_id, name, balance, account_type)
            VALUES (%s, %s, %s, %s)
        """, (session['user_id'], name, initial_amount, account_type))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if account belongs to user and is personal
        cursor.execute("""
            SELECT account_type FROM accounts 
            WHERE id = %s AND user_id = %s
        """, (account_id, session['user_id']))
        
        account = cursor.fetchone()
        if not account:
            return jsonify({'success': False, 'error': 'Account not found'})
        
        if account[0] != 'personal':
            return jsonify({'success': False, 'error': 'Cannot delete default accounts'})
        
        # Delete the account
        cursor.execute("DELETE FROM accounts WHERE id = %s AND user_id = %s", (account_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories', methods=['POST'])
@login_required
def add_category():
    data = request.json
    name = data['name']
    category_type = data['type']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO categories (user_id, name, type, is_default)
            VALUES (%s, %s, %s, FALSE)
        """, (session['user_id'], name, category_type))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if category belongs to user and is not default
        cursor.execute("""
            SELECT is_default FROM categories 
            WHERE id = %s AND user_id = %s
        """, (category_id, session['user_id']))
        
        category = cursor.fetchone()
        if not category:
            return jsonify({'success': False, 'error': 'Category not found'})
        
        if category[0]:
            return jsonify({'success': False, 'error': 'Cannot delete default categories'})
        
        # Delete the category
        cursor.execute("DELETE FROM categories WHERE id = %s AND user_id = %s", (category_id, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'error': str(e)})
