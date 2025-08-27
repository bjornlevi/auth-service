from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from .models import db, User, ServiceApiKey
from .utils import generate_token, decode_token, require_api_key


bp = Blueprint("auth", __name__, url_prefix="/api")

# ------------------------
# User Registration
# ------------------------
@bp.route("/register", methods=["POST"])
@require_api_key
def register():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")

    if not username or not password:
        return {"error": "Missing username or password"}, 400

    if email:
        existing = User.query.filter(
            or_(User.username == username, User.email == email)
        ).first()
    else:
        existing = User.query.filter_by(username=username).first()

    if existing:
        return {"error": "User with that username or email already exists"}, 400

    user = User(username=username,
                email=email,
                password=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return {"message": "User registered"}, 201


# ------------------------
# User Login
# ------------------------
@bp.route("/login", methods=["POST"])
@require_api_key
def login():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return {"error": "Missing username or password"}, 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password, password):
        return {"error": "Invalid credentials"}, 401

    token = generate_token(user.id)
    return {"token": token}, 200


# ------------------------
# Token Verification
# ------------------------
@bp.route("/verify", methods=["POST"])
@require_api_key
def verify():
    token = request.json.get("token")
    payload = decode_token(token)
    if not payload:
        return {"error": "Invalid or expired token"}, 401

    user = db.session.get(User, payload["user_id"])
    if not user:
        return {"error": "User not found"}, 404

    return {"user_id": user.id, "username": user.username}, 200


# ------------------------
# User Info
# ------------------------
@bp.route("/userinfo", methods=["POST"])
@require_api_key
def userinfo():
    token = request.json.get("token")
    payload = decode_token(token)
    if not payload:
        return {"error": "Invalid or expired token"}, 401

    user = db.session.get(User, payload["user_id"])
    if not user:
        return {"error": "User not found"}, 404

    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat()
    }, 200

# ------------------------
# Health Check
# ------------------------
@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}