FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

ENTRYPOINT ["gunicorn", "app:app", "--workers", "8", "--worker-class", "uvicorn.workers.UvicornWorker", "--timeout", "600", "--bind", "0.0.0.0:8088"]