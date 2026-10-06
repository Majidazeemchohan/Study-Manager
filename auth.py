"""Authentication: password hashing and user management."""
import hashlib
import secrets
from datetime import datetime
from database import get_connection, init_db

def _hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${h.hex()}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
    except ValueError:
        return False
    return _hash_password(password, salt) == stored

def create_user(username: str, password: str):
    """Create a new user. Returns user_id or raises ValueError if username taken."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        raise ValueError("Username already exists")
    pw_hash = _hash_password(password)
    now = datetime.now().isoformat()
    cur.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, pw_hash, now))
    user_id = cur.lastrowid
    cur.execute("INSERT INTO profiles (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    return user_id

def authenticate(username: str, password: str):
    """Return user_id if credentials valid, else None."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if row and _verify_password(password, row["password_hash"]):
        return row["id"]
    return None

def change_password(user_id: int, new_password: str):
    conn = get_connection()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                 (_hash_password(new_password), user_id))
    conn.commit()
    conn.close()
