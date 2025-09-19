FROM python:3.11-slim
WORKDIR /app

COPY app/ app/
COPY tests/ tests/ 
COPY app/requirements.txt requirements.txt

RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

ENV FLASK_APP=app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:create_app()"]

