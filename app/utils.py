import jwt
import os
import logging
from sqlalchemy import select
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from itsdangerous import URLSafeTimedSerializer
from .models import ServiceApiKey, db

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")

access_log = logging.getLogger("auth.access")

def service_name_for_key(key: str) -> str | None:
    # Avoid leaking full keys in logs
    svc = ServiceApiKey.query.filter_by(key=key).first()
    if not svc:
        return None
    # Use id or a short description in logs
    return f"id={svc.id}" + (f",desc={svc.description}" if svc.description else "")

def require_api_key(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("x-api-key")
        if not key:
            logging.getLogger("auth.access").warning("missing_api_key")
            return jsonify({"error": "Missing API key"}), 401
        svc = ServiceApiKey.query.filter_by(key=key).first()
        if not svc:
            logging.getLogger("auth.access").warning("invalid_api_key", extra={"key_suffix": key[-4:]})
            return jsonify({"error": "Invalid API key"}), 403
        g.calling_service = {"id": svc.id, "desc": svc.description}
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
