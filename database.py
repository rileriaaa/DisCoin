import psycopg2
from psycopg2 import sql
import os

def get_connection():
    """Get database connection"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        import sqlite3
        return sqlite3.connect('bot_data.db'), 'sqlite'
    
    conn = psycopg2.connect(DATABASE_URL)
    return conn, 'postgres'

def init_db():
    """Initialize the database and create tables"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id BIGINT,
                coin_name TEXT,
                asset_type TEXT DEFAULT 'crypto',
                PRIMARY KEY (user_id, coin_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                coin_name TEXT,
                target_price REAL,
                condition TEXT,
                asset_type TEXT DEFAULT 'crypto'
            )
        ''')
    else:
        # SQLite syntax (for local dev)
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
    cursor.close()
    conn.close()
    print("Database initialized!")

def migrate_db():
    """Add asset_type column to existing tables"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE watchlist ADD COLUMN asset_type TEXT DEFAULT 'crypto'")
        print("Added asset_type to watchlist")
    except:
        print("watchlist already has asset_type column")
    
    try:
        cursor.execute("ALTER TABLE alerts ADD COLUMN asset_type TEXT DEFAULT 'crypto'")
        print("Added asset_type to alerts")
    except:
        print("alerts already has asset_type column")
    
    conn.commit()
    cursor.close()
    conn.close()

def add_to_watchlist(user_id, coin_name, asset_type='crypto'):
    """Add a coin/stock to user's watchlist"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    try:
        if db_type == 'postgres':
            cursor.execute('INSERT INTO watchlist VALUES (%s, %s, %s)', (user_id, coin_name.lower(), asset_type))
        else:
            cursor.execute('INSERT INTO watchlist VALUES (?, ?, ?)', (user_id, coin_name.lower(), asset_type))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except:
        cursor.close()
        conn.close()
        return False

def remove_from_watchlist(user_id, coin_name):
    """Remove a coin/stock from user's watchlist"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('DELETE FROM watchlist WHERE user_id = %s AND coin_name = %s', (user_id, coin_name.lower()))
    else:
        cursor.execute('DELETE FROM watchlist WHERE user_id = ? AND coin_name = ?', (user_id, coin_name.lower()))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return deleted

def get_watchlist(user_id):
    """Get user's watchlist with asset types"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('SELECT coin_name, asset_type FROM watchlist WHERE user_id = %s', (user_id,))
    else:
        cursor.execute('SELECT coin_name, asset_type FROM watchlist WHERE user_id = ?', (user_id,))
    
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

def create_alert(user_id, coin_name, target_price, condition, asset_type='crypto'):
    """Create a price alert"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('INSERT INTO alerts (user_id, coin_name, target_price, condition, asset_type) VALUES (%s, %s, %s, %s, %s) RETURNING id',
                       (user_id, coin_name.lower(), target_price, condition.lower(), asset_type))
        alert_id = cursor.fetchone()[0]
    else:
        cursor.execute('INSERT INTO alerts (user_id, coin_name, target_price, condition, asset_type) VALUES (?, ?, ?, ?, ?)',
                       (user_id, coin_name.lower(), target_price, condition.lower(), asset_type))
        alert_id = cursor.lastrowid
    
    conn.commit()
    cursor.close()
    conn.close()
    return alert_id

def get_user_alerts(user_id):
    """Get all alerts for a user"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('SELECT id, coin_name, target_price, condition, asset_type FROM alerts WHERE user_id = %s', (user_id,))
    else:
        cursor.execute('SELECT id, coin_name, target_price, condition, asset_type FROM alerts WHERE user_id = ?', (user_id,))
    
    alerts = cursor.fetchall()
    cursor.close()
    conn.close()
    return alerts

def get_all_alerts():
    """Get all alerts (for background checking)"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, user_id, coin_name, target_price, condition, asset_type FROM alerts')
    alerts = cursor.fetchall()
    cursor.close()
    conn.close()
    return alerts

def delete_alert(alert_id):
    """Delete an alert by ID"""
    conn, db_type = get_connection()
    cursor = conn.cursor()
    
    if db_type == 'postgres':
        cursor.execute('DELETE FROM alerts WHERE id = %s', (alert_id,))
    else:
        cursor.execute('DELETE FROM alerts WHERE id = ?', (alert_id,))
    
    deleted = cursor.rowcount > 0
    conn.commit()
    cursor.close()
    conn.close()
    return deleted