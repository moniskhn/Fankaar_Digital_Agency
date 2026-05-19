FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements from repo root (NOT backend/)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY backend/app/ ./app/

# Copy frontend static files
COPY frontend/ ./frontend/

# Copy seed database (will be overwritten if volume mounted)
COPY data/ ./data/

ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/fankaar.db

# Ensure data directory is writable (after COPY)
RUN mkdir -p /app/data && chmod 777 /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
