from flask import Flask, redirect, url_for
from flask_login import LoginManager
from sqlalchemy import select, text
from werkzeug.security import generate_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
import secrets, logging

from .config import Config
from .models import db, ServiceApiKey, User
from .routes import bp
from .ui import ui_bp
from .logging_setup import configure_logging, install_flask_hooks
from . import db_logging

login_manager = LoginManager()

def create_app():
    # 1) init logging FIRST so bootstrap logs are structured
    configure_logging()

    app = Flask(__name__)
    app.config.from_object(Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # 2) init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "ui.login"

    # 3) request/access logging
    install_flask_hooks(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # 4) register blueprints
    api_prefix = app.config["API_PREFIX"] or ""
    ui_prefix  = app.config["UI_PREFIX"]  or ""
    app.register_blueprint(bp,   url_prefix=api_prefix)
    app.register_blueprint(ui_bp, url_prefix=ui_prefix)
    app.jinja_env.globals["ui_prefix"] = ui_prefix

    @app.route("/")
    def root_redirect():
        return redirect(url_for("ui.login"))

    @app.route("/health")
    def health_root():
        return {"status": "ok"}, 200

    @app.route("/debug/routes")
    def debug_routes():
        return {
            "APPLICATION_ROOT": app.config.get("APPLICATION_ROOT"),
            "API_PREFIX": app.config.get("API_PREFIX"),
            "UI_PREFIX": app.config.get("UI_PREFIX"),
            "routes": sorted([str(r) for r in app.url_map.iter_rules()], key=lambda s: s)
        }

    return app

def bootstrap_defaults(app):
    with app.app_context():
        # serialize bootstrap across processes/containers
        with db.engine.begin() as conn:
            got = conn.execute(text("SELECT GET_LOCK('auth_bootstrap', 60)")).scalar()
            if got != 1:
                # someone else is bootstrapping; just skip
                logging.getLogger("bootstrap").info("bootstrap_lock_skipped")
                return
            try:
                db.create_all()
                # install DB logging AFTER engine exists
                from . import db_logging
                db_logging.install(db.engine)

                default_admin = app.config["DEFAULT_ADMIN"]
                default_admin_password = app.config["DEFAULT_ADMIN_PASSWORD"]
                if not User.query.filter_by(username=default_admin).first():
                    db.session.add(User(
                        username=default_admin,
                        password=generate_password_hash(default_admin_password),
                        is_admin=True
                    ))
                    db.session.commit()
                    logging.getLogger("bootstrap").info("created_admin", extra={"username": default_admin})

                env_key = (app.config.get("AUTH_SERVICE_API_KEY") or "").strip() or None
                if env_key:
                    exists = db.session.execute(
                        select(ServiceApiKey.id).where(ServiceApiKey.key == env_key)
                    ).first()
                    if not exists:
                        db.session.add(ServiceApiKey(key=env_key, description="Env default service key"))
                        db.session.commit()
                        logging.getLogger("bootstrap").info(
                            "created_env_service_key", extra={"key_suffix": env_key[-4:]}
                        )
                else:
                    if not db.session.execute(select(ServiceApiKey.id)).first():
                        default_key = secrets.token_hex(32)  # 64 hex chars
                        db.session.add(ServiceApiKey(key=default_key, description="Default service key"))
                        db.session.commit()
                        logging.getLogger("bootstrap").info(
                            "created_random_service_key", extra={"key_suffix": default_key[-4:]}
                        )
            finally:
                conn.execute(text("SELECT RELEASE_LOCK('auth_bootstrap')"))