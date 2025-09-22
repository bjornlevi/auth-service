import os

def _norm(p: str | None) -> str:
    if not p:
        return ""
    if not p.startswith("/"):
        p = "/" + p
    return p.rstrip("/")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_KEYS = [k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip()]

    # bootstrap admin
    DEFAULT_ADMIN = os.getenv("DEFAULT_ADMIN", "admin")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "adminpass")

    URL_PREFIX = _norm(os.getenv("URL_PREFIX", ""))  # e.g. "/auth-service" or ""
    API_PREFIX = _norm(os.getenv("API_PREFIX", f"{URL_PREFIX}/api"))
    UI_PREFIX  = _norm(os.getenv("UI_PREFIX",  f"{URL_PREFIX}/ui"))

    # Flask will prepend APPLICATION_ROOT on url_for if set (useful for Option B)
    APPLICATION_ROOT = URL_PREFIX or "/"
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    }