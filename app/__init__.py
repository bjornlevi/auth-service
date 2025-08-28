from flask import Flask, current_app
from flask_login import LoginManager
from .config import Config
from .models import db, ServiceApiKey, User
from .routes import bp
from .ui import ui_bp
import secrets
from werkzeug.security import generate_password_hash

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "ui.login"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))  # SQLAlchemy 2.x safe

    with app.app_context():
        db.create_all()

        # Ensure default admin exists
        default_admin = current_app.config.get("DEFAULT_ADMIN", "admin")
        default_admin_password = current_app.config.get("DEFAULT_ADMIN_PASSWORD", "adminpass")

        if not User.query.filter_by(username=default_admin).first():
            db.session.add(User(username=default_admin,
                                password=generate_password_hash(default_admin_password),
                                is_admin=True))
            db.session.commit()
            print(f"[BOOTSTRAP] Created admin user: {default_admin} / {default_admin_password}")

        # Ensure at least one Service API key exists
        if not ServiceApiKey.query.first():
            default_key = secrets.token_hex(32)
            db.session.add(ServiceApiKey(key=default_key, description="Default service key"))
            db.session.commit()
            print(f"[BOOTSTRAP] Default Service API key created: {default_key}")

    # register blueprints
    app.register_blueprint(bp, url_prefix="/auth")  # JSON API
    app.register_blueprint(ui_bp)                   # Admin UI

    return app

