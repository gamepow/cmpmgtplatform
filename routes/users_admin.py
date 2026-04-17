from flask import request, redirect, render_template, session, flash
from server import app
from db import get_users_connection, get_data_connection, hash_password
import re

def validate_password(password):
    """
    Valida que la contraseña cumpla con los requisitos:
    - Mínimo 8 caracteres
    - Al menos una minúscula
    - Al menos una mayúscula
    - Al menos un número
    - Al menos un carácter especial
    """
    errors = []
    
    if len(password) < 8:
        errors.append("La contraseña debe tener mínimo 8 caracteres")
    
    if not re.search(r'[a-z]', password):
        errors.append("La contraseña debe contener al menos una letra minúscula")
    
    if not re.search(r'[A-Z]', password):
        errors.append("La contraseña debe contener al menos una letra mayúscula")
    
    if not re.search(r'\d', password):
        errors.append("La contraseña debe contener al menos un número")
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append("La contraseña debe contener al menos un carácter especial")
    
    return errors

@app.route('/admin/users')
def admin_users():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    conn_u = get_users_connection()
    users = conn_u.execute("SELECT * FROM users").fetchall()
    conn_u.close()

    conn_d = get_data_connection()
    companies = conn_d.execute("SELECT * FROM companies").fetchall()
    conn_d.close()

    return render_template('admin/admin_users.html', users=users, companies=companies)


@app.route('/admin/users/add', methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    company_id = request.form.get('company_id') if role == 'owner' else None
    
    # Validar contraseña
    password_errors = validate_password(password)
    if password_errors:
        for error in password_errors:
            flash(error, "danger")
        return redirect('/admin/users')
    
    conn = get_users_connection()
    try:
        if company_id:
            conn.execute(
                "INSERT INTO users (username, password, role, company_id) VALUES (?, ?, ?, ?)",
                (username, hash_password(password), role, company_id)
            )
        else:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hash_password(password), role)
            )
        conn.commit()
        flash("User created successfully.", "success")
    except Exception as e:
        flash(f"Error creating user: {str(e)}", "danger")
    finally:
        conn.close()
    
    return redirect('/admin/users')


@app.route('/admin/users/edit', methods=['POST'])
def edit_user():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    username = request.form['username']
    new_role = request.form['role']
    company_id = request.form.get('company_id') if new_role == 'owner' else None

    conn = get_users_connection()
    if company_id:
        conn.execute("UPDATE users SET role = ?, company_id = ? WHERE username = ?", (new_role, company_id, username))
    else:
        conn.execute("UPDATE users SET role = ?, company_id = NULL WHERE username = ?", (new_role, username))
    conn.commit()
    conn.close()
    flash("User updated.", "success")
    return redirect('/admin/users')


@app.route('/admin/users/delete', methods=['POST'])
def delete_user():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    username = request.form['username']
    conn = get_users_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    flash("User deleted.", "warning")
    return redirect('/admin/users')
