from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from .models import User, ServiceApiKey, db
import secrets
from .utils import generate_reset_token, verify_reset_token

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("ui.dashboard"))
    return redirect(url_for("ui.login"))


@ui_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("ui.dashboard"))
        flash("Invalid credentials")
    return render_template("login.html")


@ui_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("ui.login"))


@ui_bp.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Forbidden", 403
    keys = ServiceApiKey.query.all()
    return render_template("dashboard.html", keys=keys)


@ui_bp.route("/apikeys/add", methods=["POST"])
@login_required
def add_apikey():
    if not current_user.is_admin:
        return "Forbidden", 403
    description = request.form.get("description")
    key = secrets.token_hex(32)
    db.session.add(ServiceApiKey(key=key, description=description))
    db.session.commit()
    flash(f"Created new API key: {key}")
    return redirect(url_for("ui.dashboard"))


@ui_bp.route("/apikeys/delete/<int:key_id>", methods=["POST"])
@login_required
def delete_apikey(key_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    k = db.session.get(ServiceApiKey, key_id)
    if k:
        db.session.delete(k)
        db.session.commit()
        return jsonify({"success": True, "id": key_id})
    return jsonify({"error": "API key not found"}), 404

@ui_bp.route("/users")
@login_required
def list_users():
    if not current_user.is_admin:
        return "Forbidden", 403
    users = User.query.all()
    return render_template("users.html", users=users)


@ui_bp.route("/users/toggle/<int:user_id>", methods=["POST"])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({"success": True, "username": user.username, "is_admin": user.is_admin})


@ui_bp.route("/users/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.id == current_user.id:
        return jsonify({"error": "You cannot delete yourself"}), 400
    db.session.delete(user)
    db.session.commit()
    return jsonify({"success": True})


@ui_bp.route("/users/add", methods=["GET", "POST"])
@login_required
def add_user():
    if not current_user.is_admin:
        return "Forbidden", 403

    if request.method == "POST":
        username = request.form["username"]
        email = request.form.get("email")
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        is_admin = bool(request.form.get("is_admin"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("ui.add_user"))

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("ui.add_user"))

        user = User(username=username,
                    email=email,
                    password=generate_password_hash(password),
                    is_admin=is_admin)
        db.session.add(user)
        db.session.commit()
        flash(f"User {username} created (admin={is_admin})")
        return redirect(url_for("ui.list_users"))

    return render_template("add_user.html")


@ui_bp.route("/users/reset/<int:user_id>", methods=["POST"])
@login_required
def reset_password(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Forbidden"}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    token = generate_reset_token(user.username)
    reset_url = url_for("ui.reset_with_token", token=token, _external=True)

    return jsonify({"reset_url": reset_url})


@ui_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_with_token(token):
    username_or_email = verify_reset_token(token)
    if not username_or_email:
        flash("Invalid or expired reset link")
        return redirect(url_for("ui.login"))

    if request.method == "POST":
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("ui.reset_with_token", token=token))

        # Try by email first, then username
        user = User.query.filter_by(email=username_or_email).first() or \
               User.query.filter_by(username=username_or_email).first()
        if not user:
            flash("User not found")
            return redirect(url_for("ui.login"))

        user.password = generate_password_hash(password)
        db.session.commit()
        flash("Password updated, please log in")
        return redirect(url_for("ui.login"))

    return render_template("reset_password.html", token=token)
