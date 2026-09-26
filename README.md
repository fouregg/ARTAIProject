# ARTAI

Приложение для генерации изображений по текстовому описанию на разных языках, сохранения в галерею и показа на цифровом холсте.

## Технологии

- **Интерфейс:** React, TypeScript, Vite.
- **Сервер:** Python, FastAPI, SQLAlchemy, Alembic.
- **База данных:** PostgreSQL.
- **Генерация изображений и перевод:** AI-модели через provod.ai.
- **Окружение:** Docker и Docker Compose.

## Запуск

Понадобятся Python 3.12, Node.js 20 с npm и Docker Compose.

1. В корне проекта создайте файл настроек:

   ```bash
   cp .env.example .env
   ```

   Укажите в `.env` свой `PROVOD_API_KEY` и задайте разные значения для `DOME_TOKEN` и `ADMIN_TOKEN`.

2. Запустите базу данных и сервер из корня проекта:

   ```bash
   docker compose up -d --wait
   python3 -m venv .venv
   .venv/bin/pip install -r backend/requirements.txt
   cd backend
   ../.venv/bin/python -m uvicorn app.api.main:get_app --factory --host 0.0.0.0 --port 8000 --workers 1
   ```

3. В отдельном терминале из корня проекта запустите интерфейс:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

Откройте [http://localhost:5173](http://localhost:5173).
