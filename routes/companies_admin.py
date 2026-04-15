from flask import request, redirect, render_template, session, flash
from server import app
from db import get_data_connection, get_users_connection

@app.route('/admin/companies')
def admin_list_companies():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    conn = get_data_connection()
    companies = conn.execute("SELECT * FROM companies").fetchall()
    conn.close()

    conn_u = get_users_connection()
    available_owners = conn_u.execute(
    "SELECT id, username FROM users WHERE role = ? AND company_id IS NULL ORDER BY username",
    ("owner",)
    ).fetchall()
    conn_u.close()

    return render_template('admin/admin_companies.html', companies=companies, available_owners=available_owners)

@app.route('/admin/companies/add', methods=['GET', 'POST'])
def admin_add_company():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    if request.method == 'POST':
        company_name = (request.form.get('company_name') or '').strip()
    owner_username = (request.form.get('owner_username') or '').strip()

    if not company_name or not owner_username:
        flash("Company name and owner are required.", "danger")
        return redirect('/admin/companies')

    conn_u = get_users_connection()
    conn_d = get_data_connection()

    try:
        owner = conn_u.execute(
            "SELECT id, username, role, company_id FROM users WHERE username = ?",
            (owner_username,)
        ).fetchone()

        if not owner:
            flash("Selected owner does not exist.", "danger")
            return redirect('/admin/companies')

        if owner["role"] != "owner":
            flash("Selected user is not an owner.", "danger")
            return redirect('/admin/companies')

        if owner["company_id"] is not None:
            flash("Selected owner already has an assigned company.", "danger")
            return redirect('/admin/companies')

        cur = conn_d.execute(
            "INSERT INTO companies (name, owner) VALUES (?, ?)",
            (company_name, owner_username)
        )
        new_company_id = cur.lastrowid

        conn_u.execute(
            "UPDATE users SET company_id = ? WHERE id = ?",
            (new_company_id, owner["id"])
        )

        conn_d.commit()
        conn_u.commit()

        flash("Company created successfully.", "success")
        return redirect('/admin/companies')

    except Exception:
        conn_d.rollback()
        conn_u.rollback()
        flash("Error creating company.", "danger")
        return redirect('/admin/companies')

    finally:
        conn_d.close()
        conn_u.close()

@app.route('/admin/companies/delete', methods=['POST'])
def delete_company():
    if session.get('role') != 'admin':
        return render_template('errors/403.html'), 403
    company_id = request.form.get('company')
    if not company_id:
        flash("Invalid company.", "danger")
        return redirect('/admin/companies')

    conn_d = get_data_connection()
    conn_u = get_users_connection()

    try:
        company = conn_d.execute(
            "SELECT id, owner FROM companies WHERE id = ?",
            (company_id,)
        ).fetchone()

        if not company:
            flash("Company not found.", "danger")
            return redirect('/admin/companies')

        conn_d.execute("DELETE FROM comments WHERE company_id = ?", (company_id,))
        conn_d.execute("DELETE FROM companies WHERE id = ?", (company_id,))

        # Desenlaza owner -> company_id
        conn_u.execute(
            "UPDATE users SET company_id = NULL WHERE username = ? AND company_id = ?",
            (company["owner"], company_id)
        )

        conn_d.commit()
        conn_u.commit()

        flash("Company deleted.", "warning")
        return redirect('/admin/companies')

    except Exception:
        conn_d.rollback()
        conn_u.rollback()
        flash("Error deleting company.", "danger")
        return redirect('/admin/companies')

    finally:
        conn_d.close()
        conn_u.close()
