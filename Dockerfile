FROM python:3.11-slim
WORKDIR /app

COPY app/ app/
COPY tests/ tests/ 
COPY app/requirements.txt requirements.txt

RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

ENV FLASK_APP=app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]

