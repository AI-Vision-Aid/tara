FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8080 COOKIE_SECURE=1
CMD exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 90
