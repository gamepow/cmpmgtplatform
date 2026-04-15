import os
from datetime import timedelta
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
import logging

app = Flask(__name__)

#app.logger.setLevel(logging.DEBUG)

# Si secret key no esta definida, la aplicación no inicia y lanza un error al desarrollador.
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY no está definida en variables de entorno")

app.config["SECRET_KEY"] = secret_key
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Configuración de cookies de sesión
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True

csrf = CSRFProtect(app)

@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403