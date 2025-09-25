FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV VENV_PATH=/opt/venv
RUN python -m venv "$VENV_PATH"
ENV PATH="$VENV_PATH/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ /app/app
COPY wsgi.py /app/wsgi.py

RUN useradd -m -u 10001 app \
 && mkdir -p /app/logs \
 && chown -R 10001:10001 /app "$VENV_PATH"
USER app

ENV PYTHONPATH=/app FLASK_APP=app
CMD ["gunicorn","--preload","-b","0.0.0.0:5000","-w","2","--log-level","info","wsgi:app"]

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).getcode()==200 else 1)"
