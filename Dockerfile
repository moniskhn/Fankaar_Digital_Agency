FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libsqlite3-dev && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/

ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/mythos.db

RUN mkdir -p /app/data && chmod 777 /app/data

EXPOSE 8000

COPY backend/start.sh ./start.sh
RUN chmod +x ./start.sh
CMD ["./start.sh"]
