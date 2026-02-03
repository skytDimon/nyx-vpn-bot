FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY alembic.ini /app/alembic.ini
COPY alembic /app/alembic
COPY img /app/img
COPY app /app/app

ENV PYTHONPATH=/app
CMD ["python", "-m", "app.main"]
