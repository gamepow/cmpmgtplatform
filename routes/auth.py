import time
import math

from urllib.parse import urlparse, urljoin
from db import get_users_connection, hash_password
from flask import request, redirect, render_template, session, flash
from server import app

# Parametros de seguridad para login - deben ser actualizados para un ambiente de PRD
MAX_LOGIN_ATTEMPTS = 3
WINDOW_SECONDS = 60
LOCK_SECONDS = 600

def _human_lock_time(seconds):
    if seconds < 60:
        unit = "second" if seconds == 1 else "seconds"
        return f"{seconds} {unit}"

    minutes = math.ceil(seconds / 60)
    unit = "minute" if minutes == 1 else "minutes"
    return f"{minutes} {unit}"

def _get_client_ip():
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _build_attempt_key(username):
    uname = (username or "").strip().lower()
    ip = _get_client_ip()
    return f"{uname}|{ip}"


def _is_safe_next_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect('/dashboard')

    next_url = request.args.get('next', '/dashboard')
    if not _is_safe_next_url(next_url):
        next_url = '/dashboard'

    if request.method == 'POST':
        username = (request.form.get('username') or "").strip()
        password = request.form.get('password') or ""

        if not username or not password:
            flash("Invalid username or password", "danger")
            return render_template('auth/login.html', next_url=next_url), 400

        now = int(time.time())
        attempt_key = _build_attempt_key(username)

        conn = get_users_connection()

        attempt = conn.execute(
            "SELECT fail_count, window_start, lock_until FROM login_attempts WHERE attempt_key = ?",
            (attempt_key,)
        ).fetchone()

        fail_count = 0
        window_start = now
        lock_until = 0

        if attempt:
            fail_count = attempt["fail_count"] or 0
            window_start = attempt["window_start"] or now
            lock_until = attempt["lock_until"] or 0

            if lock_until and now < lock_until:
                conn.close()
                flash(f"Too many failed attempts. Try again in {_human_lock_time(LOCK_SECONDS)}.", "danger")
                return render_template('auth/login.html', next_url=next_url), 429

            # Reinicia ventana si ya expiró
            if now - window_start > WINDOW_SECONDS:
                fail_count = 0
                window_start = now
                lock_until = 0

        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, hash_password(password))
        ).fetchone()

        if user:
            # Login correcto: limpiar contador de intentos
            conn.execute("DELETE FROM login_attempts WHERE attempt_key = ?", (attempt_key,))
            conn.commit()
            conn.close()

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['company_id'] = user['company_id']
            session.permanent = True
            return redirect(next_url)

        # Login fallido
        fail_count += 1
        new_lock_until = None

        if fail_count >= MAX_LOGIN_ATTEMPTS:
            new_lock_until = now + LOCK_SECONDS
            fail_count = 0
            window_start = now

        if attempt:
            conn.execute(
                "UPDATE login_attempts SET fail_count = ?, window_start = ?, lock_until = ? WHERE attempt_key = ?",
                (fail_count, window_start, new_lock_until, attempt_key)
            )
        else:
            conn.execute(
                "INSERT INTO login_attempts (attempt_key, fail_count, window_start, lock_until) VALUES (?, ?, ?, ?)",
                (attempt_key, fail_count, window_start, new_lock_until)
            )

        conn.commit()
        conn.close()

        if new_lock_until:
            flash(f"Too many failed attempts. Try again in {_human_lock_time(LOCK_SECONDS)}.", "danger")
            return render_template('auth/login.html', next_url=next_url), 429

        flash("Invalid username or password", "danger")
        return render_template('auth/login.html', next_url=next_url)

    return render_template('auth/login.html', next_url=next_url)


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')