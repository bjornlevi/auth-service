# app/logging_setup.py
import json, logging, os, sys, time, uuid
from contextvars import ContextVar
from datetime import datetime, timezone

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

SENSITIVE_KEYS = {"password", "token", "access_token", "refresh_token", "x-api-key", "authorization"}

def _mask(val):
    if val is None: return None
    s = str(val)
    return "****" if len(s) <= 8 else s[:2] + "****" + s[-2:]

def _scrub_dict(d):
    if not isinstance(d, dict): return d
    out = {}
    for k, v in d.items():
        if k.lower() in SENSITIVE_KEYS:
            out[k] = _mask(v)
        else:
            out[k] = v
    return out

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
KNOWN_EXTRA = {
    "method","path","endpoint","status","ok","latency_ms","remote_addr","user_agent",
    "headers","json","service","duration_ms","statement","parameters"
}

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": _request_id.get(),
        }

        # Only copy **known** extras; coerce non-serializable values to str
        rdict = record.__dict__
        for key in KNOWN_EXTRA:
            if key in rdict:
                val = rdict[key]
                try:
                    json.dumps(val)           # probe serializability
                    payload[key] = val
                except Exception:
                    payload[key] = str(val)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Final dump must never fail
        return json.dumps(payload, ensure_ascii=False, default=str)

def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

    logging.getLogger("werkzeug").setLevel(os.getenv("WERKZEUG_LOG_LEVEL", "WARNING").upper())
    logging.getLogger("sqlalchemy.engine").setLevel(os.getenv("SQL_LOG_LEVEL", "WARNING").upper())
    logging.getLogger("sqlalchemy.pool").setLevel(os.getenv("SQL_POOL_LOG_LEVEL", "INFO").upper())

def install_flask_hooks(app):
    from flask import request, g

    access = logging.getLogger("access")

    @app.before_request
    def _before():
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        _request_id.set(rid)
        g._t0 = time.perf_counter()

    @app.after_request
    def _after(resp):
        t1 = time.perf_counter()
        latency_ms = round((t1 - getattr(g, "_t0", t1)) * 1000, 2)

        # caller ip: if you add a reverse proxy later, X-Forwarded-For will be honored here
        caller = request.headers.get("X-Forwarded-For") or request.remote_addr

        # scrub input
        json_body = request.get_json(silent=True) if request.is_json else None
        json_body = _scrub_dict(json_body) if isinstance(json_body, dict) else None

        headers = {}
        for k, v in request.headers.items():
            lk = k.lower()
            if lk == "cookie":
                continue
            # mask sensitive if you do that; keep as plain str
            headers[k] = str(v)

        # Ensure json body is a plain dict (or None)
        body = request.get_json(silent=True) if request.is_json else None
        if not isinstance(body, dict):
            body = None  # avoid lists/complex types in access log

        try:
            access.info("request", extra=dict(
                method=request.method,
                path=request.path,
                endpoint=request.endpoint,
                status=resp.status_code,
                ok=(200 <= resp.status_code < 400),
                latency_ms=latency_ms,
                remote_addr=request.headers.get("X-Forwarded-For") or request.remote_addr,
                user_agent=request.user_agent.string,
                headers=headers,
                json=body,
            ))
        except Exception:
            # fallback in case something in extra breaks JSON serialization
            logging.getLogger("access-fallback").warning(
                "access_log_failed", exc_info=True
            )
        # surface the request id for callers
        resp.headers["X-Request-ID"] = _request_id.get()
        return resp

    @app.errorhandler(Exception)
    def _log_ex(e):
        logging.getLogger("app").exception("unhandled_exception")
        raise

    return app
