# Additional routes for user settings management
# This should be added to the main app.py file

@app.route('/api/user-settings')
@login_required
def get_user_settings():
    """Get current user settings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT email_notifications FROM users WHERE id = %s", (session['user_id'],))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            return jsonify({
                'email_notifications': bool(result[0])
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return jsonify({'error': 'Failed to load settings'}), 500

@app.route('/api/user-settings', methods=['POST'])
@login_required
def update_user_settings():
    """Update user settings"""
    try:
        data = request.json
        email_notifications = data.get('email_notifications', False)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE users SET email_notifications = %s WHERE id = %s",
            (email_notifications, session['user_id'])
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Error updating user settings: {e}")
        return jsonify({'success': False, 'error': 'Failed to update settings'}), 500
