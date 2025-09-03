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

    API_PREFIX = ""
    UI_PREFIX = ""
