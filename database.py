import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            user_id INTEGER,
            coin_name TEXT,
            asset_type TEXT DEFAULT 'crypto',
            PRIMARY KEY (user_id, coin_name)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            coin_name TEXT,
            target_price REAL,
            condition TEXT,
            asset_type TEXT DEFAULT 'crypto'
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized!")

def add_to_watchlist(user_id, coin_name, asset_type='crypto'):
    """Add a coin/stock to user's watchlist"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO watchlist VALUES (?, ?, ?)', (user_id, coin_name.lower(), asset_type))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def remove_from_watchlist(user_id, coin_name):
    """Remove a coin/stock from user's watchlist"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM watchlist WHERE user_id = ? AND coin_name = ?', 
                   (user_id, coin_name.lower()))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_watchlist(user_id):
    """Get user's watchlist with asset types"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT coin_name, asset_type FROM watchlist WHERE user_id = ?', (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items

def create_alert(user_id, coin_name, target_price, condition, asset_type='crypto'):
    """Create a price alert"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('INSERT INTO alerts (user_id, coin_name, target_price, condition, asset_type) VALUES (?, ?, ?, ?, ?)',
                   (user_id, coin_name.lower(), target_price, condition.lower(), asset_type))
    
    alert_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def get_user_alerts(user_id):
    """Get all alerts for a user"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, coin_name, target_price, condition, asset_type FROM alerts WHERE user_id = ?', (user_id,))
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def get_all_alerts():
    """Get all alerts (for background checking)"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, user_id, coin_name, target_price, condition, asset_type FROM alerts')
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def delete_alert(alert_id):
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted