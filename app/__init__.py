from flask import Flask, current_app
from flask_login import LoginManager
from .config import Config
from .models import db, ServiceApiKey, User
from .routes import bp
from .ui import ui_bp
import secrets
from werkzeug.security import generate_password_hash

login_manager = LoginManager()
# Load environment variables from .env before anything else

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
        default_admin = current_app.config["DEFAULT_ADMIN"]
        default_admin_password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

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
    api_prefix = app.config.get("API_PREFIX", "/auth")
    app.jinja_env.globals["api_prefix"] = api_prefix
    ui_prefix = app.config.get("UI_PREFIX", "")  # "" = root by default

    app.register_blueprint(bp, url_prefix=api_prefix)
    app.register_blueprint(ui_bp, url_prefix=ui_prefix)

    return app

