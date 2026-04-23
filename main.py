import os
from server import app
from routes import auth, companies, companies_admin, users_admin, profile

def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

if __name__ == "__main__":
    debug_mode = _env_bool("FLASK_DEBUG", False)
    app.run(debug=debug_mode, use_reloader=debug_mode)