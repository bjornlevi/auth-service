from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User
from .utils import generate_token, decode_token, require_api_key
import secrets

bp = Blueprint("auth", __name__, url_prefix="/api")

# ------------------------
# User Registration
# ------------------------
@bp.route("/register", methods=["POST"])
@require_api_key
def register():
    data = request.json
    if not data or not data.get("username") or not data.get("password"):
        return {"error": "Missing username or password"}, 400

    if User.query.filter_by(username=data["username"]).first():
        return {"error": "User already exists"}, 400

    hashed_pw = generate_password_hash(data["password"])
    user = User(username=data["username"], password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return {"message": "User registered"}, 201


# ------------------------
# User Login
# ------------------------
@bp.route("/login", methods=["POST"])
@require_api_key
def login():
    data = request.json
    if not data or not data.get("username") or not data.get("password"):
        return {"error": "Missing username or password"}, 400

    user = User.query.filter_by(username=data["username"]).first()
    if not user or not check_password_hash(user.password, data["password"]):
        return {"error": "Invalid credentials"}, 401

    token = generate_token(user.id)
    return {"token": token}


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

    return {"user_id": user.id, "username": user.username}

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
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at.isoformat()
    }

# ------------------------
# Health Check
# ------------------------
@bp.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}
