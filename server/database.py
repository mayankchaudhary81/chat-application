import sqlite3
import hashlib
import os
import json

DB_PATH = 'users.db'

def hash_password(password: str) -> str:
    # Use PBKDF2 for password hashing
    salt = b'super_secret_salt' # In production, this should be a random salt stored in the DB alongside the hash
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return key.hex()

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            text TEXT,
            msg_type TEXT DEFAULT 'text',
            file_data TEXT,
            timestamp TEXT NOT NULL,
            is_edited BOOLEAN DEFAULT 0,
            deleted BOOLEAN DEFAULT 0,
            read_by TEXT DEFAULT '[]'
        )
    ''')
    conn.commit()
    conn.close()

def register_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        hashed = hash_password(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, hashed))
        conn.commit()
        conn.close()
        return True, "Registration successful."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, str(e)

def authenticate_user(username, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            stored_hash = row[0]
            if stored_hash == hash_password(password):
                return True, "Login successful."
        return False, "Invalid username or password."
    except Exception as e:
        return False, str(e)

def save_message(msg_id, username, text, msg_type, file_data, timestamp):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (id, username, text, msg_type, file_data, timestamp, is_edited, deleted, read_by)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0, '[]')
        ''', (msg_id, username, text, msg_type, file_data, timestamp))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error saving message: {e}")
        return False

def get_messages(limit=50):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, text, msg_type, file_data, timestamp, is_edited, deleted, read_by 
            FROM messages 
            ORDER BY timestamp ASC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        messages = []
        for row in rows:
            messages.append({
                "id": row[0],
                "username": row[1],
                "text": row[2],
                "msg_type": row[3],
                "file_data": row[4],
                "timestamp": row[5],
                "is_edited": bool(row[6]),
                "deleted": bool(row[7]),
                "read_by": json.loads(row[8]) if row[8] else []
            })
        return messages
    except Exception as e:
        print(f"DB Error fetching messages: {e}")
        return []

def update_message(msg_id, new_text):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE messages SET text = ?, is_edited = 1 WHERE id = ?', (new_text, msg_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error updating message: {e}")
        return False

def delete_message(msg_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Set to deleted and blank out file data for privacy, but keep text field minimal or a placeholder
        cursor.execute("UPDATE messages SET deleted = 1, text = '🚫 This message was deleted', file_data = NULL WHERE id = ?", (msg_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error deleting message: {e}")
        return False

def mark_message_read(msg_id, username):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT read_by FROM messages WHERE id = ?', (msg_id,))
        row = cursor.fetchone()
        if row:
            read_by = json.loads(row[0]) if row[0] else []
            if username not in read_by:
                read_by.append(username)
                cursor.execute('UPDATE messages SET read_by = ? WHERE id = ?', (json.dumps(read_by), msg_id))
                conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"DB Error tracking read receipt: {e}")
        return False

initialize_db()
