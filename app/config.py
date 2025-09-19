import os

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

    # be prefix aware if the app lives in /some-folder
    API_PREFIX = os.getenv("API_PREFIX", "/api")
    UI_PREFIX = os.getenv("UI_PREFIX", "/ui")
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
    }