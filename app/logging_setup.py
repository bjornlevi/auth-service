# app/logging_setup.py
import json
import logging
import os
import time
import uuid
from logging import StreamHandler, FileHandler
from flask import request, g

REDACT_KEYS = {"authorization", "x-api-key", "password", "token"}

class JsonFormatter(logging.Formatter):
    def format(self, record):
        # base
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{int(time.time()*1000)%1000:03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # merge record.extra (from logger.*(..., extra={...}))
        for k, v in getattr(record, "__dict__", {}).items():
            if k in ("args","asctime","created","exc_info","exc_text","filename","funcName",
                     "levelname","levelno","lineno","module","msecs","message","msg","name",
                     "pathname","process","processName","relativeCreated","stack_info","thread",
                     "threadName"):
                continue
            payload[k] = v
        # exception
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def _ensure_handler(logger, handler):
    if not any(isinstance(h, handler.__class__) for h in logger.handlers):
        logger.addHandler(handler)

def configure_logging():
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = os.getenv("LOG_FILE")
    root = logging.getLogger()
    root.setLevel(level)

    fmt = JsonFormatter()
    sh = StreamHandler()
    sh.setFormatter(fmt)
    _ensure_handler(root, sh)

    if log_file:
        fh = FileHandler(log_file)
        fh.setFormatter(fmt)
        _ensure_handler(root, fh)

def _redact_headers(h):
    out = {}
    for k, v in h.items():
        if k.lower() in REDACT_KEYS:
            if k.lower() == "x-api-key" and isinstance(v, str) and len(v) >= 4:
                out[k] = f"***{v[-4:]}"      # keep last 4 for correlation
            else:
                out[k] = "****"
        else:
            out[k] = v
    return out

def install_flask_hooks(app):
    access = logging.getLogger("access")

    @app.before_request
    def _start():
        g._t0 = time.time()
        # use incoming X-Request-ID or generate one
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_id = rid

    @app.after_request
    def _after(response):
        try:
            dt = (time.time() - getattr(g, "_t0", time.time())) * 1000.0
            # propagate request id back
            response.headers["X-Request-ID"] = getattr(g, "request_id", "")
            # pick a few useful headers; dump all if you prefer
            hdrs = {
                "Host": request.headers.get("Host"),
                "X-Forwarded-For": request.headers.get("X-Forwarded-For"),
                "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto"),
                "X-Api-Key": request.headers.get("X-Api-Key"),
                "User-Agent": request.headers.get("User-Agent"),
            }
            access.info(
                "request",
                extra={
                    "request_id": g.request_id,
                    "method": request.method,
                    "path": request.full_path.rstrip("?"),
                    "status": response.status_code,
                    "latency_ms": round(dt, 2),
                    "remote_addr": request.headers.get("X-Forwarded-For", request.remote_addr),
                    "user_agent": request.headers.get("User-Agent"),
                    "headers": _redact_headers(hdrs),
                },
            )
        except Exception:
            # never break the response because of logging
            logging.getLogger("access").exception("access_log_error")
        return response

    @app.errorhandler(Exception)
    def _on_error(err):
        logging.getLogger("app").exception(
            "unhandled_exception",
            extra={"request_id": getattr(g, "request_id", None)}
        )
        return jsonify(error="internal_server_error"), 500
