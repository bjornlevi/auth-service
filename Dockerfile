# ---------- Base builder (installs prod deps into a venv) ----------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps (build tools for wheels + curl for health/debug)
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
 && rm -rf /var/lib/apt/lists/*

# Create a virtualenv and use it for all subsequent RUN/CMD
ENV VENV_PATH=/opt/venv
RUN python -m venv "$VENV_PATH"
ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /app

# Install prod requirements first to leverage Docker layer caching
COPY requirements.txt requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# ---------- Runtime (lean) ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy the prebuilt venv from the base stage
ENV VENV_PATH=/opt/venv
COPY --from=base $VENV_PATH $VENV_PATH
ENV PATH="$VENV_PATH/bin:$PATH"

# App files
WORKDIR /app
COPY app/ /app/app
COPY wsgi.py /app/wsgi.py

# (Optional) non-root user
RUN useradd -m -u 10001 app && chown -R app:app /app
USER app

ENV PYTHONPATH=/app \
    FLASK_APP=app

# Gunicorn (prod)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "wsgi:app"]

# Flat /health inside the container
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).getcode()==200 else 1)"

# ---------- Dev image (adds test deps + tests) ----------
FROM runtime AS dev
USER root
COPY requirements-dev.txt /app/requirements-dev.txt
RUN "$VENV_PATH/bin/pip" install -r /app/requirements-dev.txt
USER app

# (Optional) include tests in the dev image only
COPY tests/ /app/tests/
