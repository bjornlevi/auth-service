FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl

WORKDIR /app

COPY app/ app/
COPY tests/ tests/ 
COPY app/requirements.txt requirements.txt


RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

ENV FLASK_APP=app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:create_app()"]

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2).getcode()==200 else 1)"
