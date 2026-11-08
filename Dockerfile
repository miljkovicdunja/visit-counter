FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8080

WORKDIR /app

RUN useradd --create-home --uid 1000 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER appuser

EXPOSE 8080

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${APP_PORT} --workers 2 app:app"]