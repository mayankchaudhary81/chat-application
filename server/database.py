import sqlite3
import hashlib
import os

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

initialize_db()
