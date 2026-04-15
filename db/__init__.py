import sqlite3
import os
import hashlib
import bcrypt

DB_DIR = os.path.join(os.path.dirname(__file__), '..', 'db')
USERS_DB = os.path.join(DB_DIR, 'users.db')
DATA_DB = os.path.join(DB_DIR, 'data.db')

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, stored_hash):
    if not stored_hash:
        return False, False

    if stored_hash.startswith("$2a$") or stored_hash.startswith("$2b$") or stored_hash.startswith("$2y$"):
        ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
        return ok, False

    # Se incluye verificación con usuarios que tenian el password con MD5
    legacy_ok = hashlib.md5(password.encode()).hexdigest() == stored_hash
    # Si fue MD5 válido, pedir rehash a BCrypt
    return legacy_ok, legacy_ok

def ensure_users_db():
    # Primero, asegurarse de que las tablas de datos existen (empresas, comentarios)
    ensure_data_db()
    
    # Ahora procedemos a crear los usuarios
    if not os.path.exists(USERS_DB):
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(USERS_DB)
        c = conn.cursor()
        c.execute("""CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            company_id INTEGER
        )""")
        users = [
            ('alice', hash_password('password1'), 'user', None),
            ('bob', hash_password('password2'), 'owner', 1),  # Bob es owner y su empresa tiene ID 1
            ('admin', hash_password('admin123'), 'admin', None)
        ]
        c.executemany("INSERT INTO users (username, password, role, company_id) VALUES (?, ?, ?, ?)", users)
        
        c.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
            attempt_key TEXT PRIMARY KEY,
            fail_count INTEGER NOT NULL DEFAULT 0,
            window_start INTEGER NOT NULL,
            lock_until INTEGER
        )""")

        conn.commit()
        conn.close()


def ensure_data_db():
    if not os.path.exists(DATA_DB):
        os.makedirs(DB_DIR, exist_ok=True)
        conn = sqlite3.connect(DATA_DB)
        c = conn.cursor()
        c.execute("""CREATE TABLE companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            owner TEXT
        )""")
        c.execute("""CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            user TEXT,
            comment TEXT
        )""")
        c.execute("INSERT INTO companies (name, description, owner) VALUES ('Insegura Corp', 'A very insecure company.', 'bob')")

        c.execute("INSERT INTO comments (company_id, user, comment) VALUES (1, 'alice', 'This company is extremely insecure!')")
        c.execute("INSERT INTO comments (company_id, user, comment) VALUES (1, 'admin', 'I agree, there are many vulnerabilities here.')")
        c.execute("INSERT INTO comments (company_id, user, comment) VALUES (1, 'bob', 'We need to improve security immediately.')")
        
         # Insertar la empresa Flameera
        c.execute("INSERT INTO companies (name, description, owner) VALUES ('Flameera', 'A cutting-edge company with top security measures.', 'bob')")

        # Insertar comentarios de ejemplo para Flameera
        c.execute("INSERT INTO comments (company_id, user, comment) VALUES (2, 'alice', 'Flameera is doing great with security!')")
        c.execute("INSERT INTO comments (company_id, user, comment) VALUES (2, 'admin', 'Top-tier measures! I recommend this company for security.')")
        c.execute("INSERT INTO comments (company_id, user, comment) VALUES (2, 'bob', 'Our security is state-of-the-art! Flameera is the future.')")


        conn.commit()
        conn.close()

def get_users_connection():
    ensure_users_db()
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn

def get_data_connection():
    ensure_data_db()
    conn = sqlite3.connect(DATA_DB)
    conn.row_factory = sqlite3.Row
    return conn
