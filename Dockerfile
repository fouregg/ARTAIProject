# --- сборка фронтенда -------------------------------------------------------
FROM node:20-alpine AS frontend

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

# --- рантайм ----------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ backend/
# Политику обработки ПДН приложение отдаёт файлом из docs/ (см. services/legal.py).
COPY docs/ docs/
COPY --from=frontend /app/frontend/dist frontend/dist

# Каталог с картинками монтируется томом, но должен существовать и на пустом томе.
RUN mkdir -p /app/storage

WORKDIR /app/backend
EXPOSE 8000

# Хаб подключений цифрового холста живёт в памяти процесса — только один воркер.
CMD ["python", "-m", "uvicorn", "app.api.main:get_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
