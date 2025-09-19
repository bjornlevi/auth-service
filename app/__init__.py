from flask import Flask, current_app, redirect, url_for
from flask_login import LoginManager
from .config import Config
from .models import db, ServiceApiKey, User
from .routes import bp
from .ui import ui_bp
import secrets
from werkzeug.security import generate_password_hash

# NEW
from .logging_setup import configure_logging, install_flask_hooks
from . import db_logging

login_manager = LoginManager()

def create_app():
    # 1) init logging FIRST so bootstrap logs are structured
    configure_logging()

    app = Flask(__name__)
    app.config.from_object(Config)

    # 2) init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "ui.login"

    # 3) request/access logging
    install_flask_hooks(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

        # 3b) install DB logging once engine exists
        db_logging.install(db.engine)

        # Bootstrap admin & API key (these prints will now be JSON logs if you want)
        default_admin = current_app.config["DEFAULT_ADMIN"]
        default_admin_password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

        if not User.query.filter_by(username=default_admin).first():
            db.session.add(User(username=default_admin,
                                password=generate_password_hash(default_admin_password),
                                is_admin=True))
            db.session.commit()
            # Optional: use logging instead of print
            import logging
            logging.getLogger("bootstrap").info("created_admin", extra={"username": default_admin})

        if not ServiceApiKey.query.first():
            default_key = secrets.token_hex(32)
            db.session.add(ServiceApiKey(key=default_key, description="Default service key"))
            db.session.commit()
            import logging
            logging.getLogger("bootstrap").info("created_default_service_key", extra={"key_suffix": default_key[-4:]})

    # 4) register blueprints
    api_prefix = app.config.get("API_PREFIX", "/auth")
    ui_prefix = app.config.get("UI_PREFIX", "")
    app.register_blueprint(bp, url_prefix=api_prefix)
    app.register_blueprint(ui_bp, url_prefix=ui_prefix)
    app.jinja_env.globals["ui_prefix"] = ui_prefix

    @app.route("/")
    def root_redirect():
        return redirect(url_for("ui.login"))

    return app
