from flask import Flask, render_template
from datetime import timedelta
from flask_wtf.csrf import CSRFProtect


app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.permanent_session_lifetime = timedelta(minutes=30)

csrf = CSRFProtect(app)
csrf.init_app(app)

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

