import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from itsdangerous import URLSafeTimedSerializer
from .models import ServiceApiKey, db

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if not key:
            return jsonify({"error": "Missing API key"}), 401
        if not ServiceApiKey.query.filter_by(key=key).first():
            return jsonify({"error": "Invalid API key"}), 403
        return f(*args, **kwargs)
    return decorated

def generate_token(user_id):
    payload = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=2)}
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    if isinstance(token, bytes):  # PyJWT < 2
        token = token.decode("utf-8")
    return token


def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except Exception:
        return None

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if not key or not ServiceApiKey.query.filter_by(key=key).first():
            return jsonify({"error": "Invalid API key"}), 403
        return f(*args, **kwargs)
    return decorated

def generate_reset_token(email, expires_sec=3600):
    s = URLSafeTimedSerializer(SECRET_KEY)
    return s.dumps(email, salt="password-reset")

def verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = s.loads(token, salt="password-reset", max_age=max_age)
    except Exception:
        return None
    return email
