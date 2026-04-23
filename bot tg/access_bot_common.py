import os
import secrets
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip() or os.getenv('TELEGRAM_TOKEN', '').strip()
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '').strip()
SECRET_KEY = os.getenv('SECRET_KEY', '').strip() or secrets.token_urlsafe(32)
COINMARKETCAP_API_URL = os.getenv('COINMARKETCAP_API_URL', 'https://pro-api.coinmarketcap.com').strip()
COINMARKETCAP_API_KEY = os.getenv('COINMARKETCAP_API_KEY', '').strip()
ADMIN_TELEGRAM_IDS = {
    int(user_id.strip())
    for user_id in os.getenv('ADMIN_TELEGRAM_IDS', '').split(',')
    if user_id.strip().isdigit()
}
DB_PATH = os.getenv('ACCESS_DB_PATH', 'bot_access.db')
ADMIN_PANEL_HOST = os.getenv('ADMIN_PANEL_HOST', '0.0.0.0')
ADMIN_PANEL_PORT = int(os.getenv('ADMIN_PANEL_PORT', '5000'))

if not BOT_TOKEN:
    raise RuntimeError('BOT_TOKEN is missing in .env. Встановіть TELEGRAM_BOT_TOKEN.')

if not ADMIN_PASSWORD:
    raise RuntimeError('ADMIN_PASSWORD is missing in .env. Встановіть ADMIN_PASSWORD.')

# Захист доступу до бази даних, коли працює кілька потоків.
db_lock = threading.Lock()

CREATE_USERS_TABLE = '''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    role TEXT NOT NULL DEFAULT 'guest',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''

CREATE_ACCESS_LOG_TABLE = '''
CREATE TABLE IF NOT EXISTS access_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER NOT NULL,
    event TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(CREATE_USERS_TABLE)
        cursor.execute(CREATE_ACCESS_LOG_TABLE)
        conn.commit()
        conn.close()

    for telegram_id in ADMIN_TELEGRAM_IDS:
        add_or_update_user(
            telegram_id=telegram_id,
            username='admin',
            first_name='Admin',
            last_name=None,
            role='admin',
            status='active'
        )


def add_or_update_user(
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    role: str = 'guest',
    status: str = 'active'
) -> None:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat(sep=' ', timespec='seconds')
        cursor.execute('SELECT role, status FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                'INSERT INTO users (telegram_id, username, first_name, last_name, role, status, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (telegram_id, username, first_name, last_name, role, status, now)
            )
        else:
            if telegram_id in ADMIN_TELEGRAM_IDS:
                role = 'admin'
                status = 'active'
            cursor.execute(
                'UPDATE users SET username = ?, first_name = ?, last_name = ?, role = ?, status = ?, updated_at = ? WHERE telegram_id = ?',
                (username, first_name, last_name, role, status, now, telegram_id)
            )
        conn.commit()
        conn.close()


def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        row = cursor.fetchone()
        conn.close()
    return dict(row) if row else None


def update_user_role_status(telegram_id: int, role: str, status: str) -> bool:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET role = ?, status = ?, updated_at = ? WHERE telegram_id = ?',
            (role, status, datetime.utcnow().isoformat(sep=' ', timespec='seconds'), telegram_id)
        )
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
    return rowcount > 0


def remove_user(telegram_id: int) -> bool:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE telegram_id = ?', (telegram_id,))
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
    return rowcount > 0


def list_users() -> List[Dict]:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY updated_at DESC')
        rows = cursor.fetchall()
        conn.close()
    return [dict(row) for row in rows]


def log_event(telegram_id: int, event: str, details: str | None = None) -> None:
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO access_logs (telegram_id, event, details) VALUES (?, ?, ?)',
            (telegram_id, event, details)
        )
        conn.commit()
        conn.close()


def is_admin_user(telegram_id: int) -> bool:
    user = get_user_by_telegram_id(telegram_id)
    return bool(user and user['role'] == 'admin' and user['status'] == 'active')


def is_banned_user(telegram_id: int) -> bool:
    user = get_user_by_telegram_id(telegram_id)
    return bool(user and user['status'] == 'banned')
