#!/usr/bin/env bash
# Подготовка сервера под автодеплой. Запускается один раз от root:
#
#   DEPLOY_PUBKEY='ssh-ed25519 AAAA... github-actions-artai-deploy' \
#     bash <(curl -fsSL https://raw.githubusercontent.com/fouregg/ARTAIProject/main/deploy/bootstrap.sh)
#
# DEPLOY_PUBKEY — публичная часть ключа, приватная лежит в секрете DEPLOY_SSH_KEY.
# Можно передать несколько ключей через перевод строки.
# Скрипт идемпотентный: повторный запуск ничего не ломает и не перезаписывает .env.
set -euo pipefail

APP_DIR=/opt/artai
COMPOSE_URL=https://raw.githubusercontent.com/fouregg/ARTAIProject/main/deploy/docker-compose.yml

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

if [[ $EUID -ne 0 ]]; then
  echo "Запускать нужно от root" >&2
  exit 1
fi

say "1. Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
else
  echo "уже установлен: $(docker --version)"
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Плагин docker compose не найден — поставьте docker-compose-plugin" >&2
  exit 1
fi

say "2. Каталог приложения"
mkdir -p "$APP_DIR"
cd "$APP_DIR"
curl -fsSL "$COMPOSE_URL" -o docker-compose.yml
echo "$APP_DIR/docker-compose.yml обновлён"

say "3. Файл .env"
if [[ -f .env ]]; then
  echo ".env уже есть — оставляю как есть"
else
  db_password="$(openssl rand -hex 24)"
  dome_token="$(openssl rand -hex 24)"
  cat > .env <<ENV
POSTGRES_USER=artai
POSTGRES_PASSWORD=${db_password}
POSTGRES_DB=artai
DATABASE_URL=postgresql+asyncpg://artai:${db_password}@postgres:5432/artai

PROVOD_API_KEY=ЗАПОЛНИТЕ
PROVOD_BASE_URL=https://api.provod.ai/v1
PROVOD_IMAGE_MODEL=openai/gpt-image-2
PROVOD_TEXT_MODEL=google/gemini-3.1-flash-lite

DOME_TOKEN=${dome_token}
TERMINAL_ID=terminal-1

STORAGE_DIR=/app/storage
CODE_GENERATIONS_LIMIT=10
IMAGE_TTL_MINUTES=60
CLEANUP_INTERVAL_MINUTES=10
AUTO_MIGRATE=true
CORS_ORIGINS=

APP_IMAGE=ghcr.io/fouregg/artaiproject:latest
ENV
  chmod 600 .env
  echo "создан $APP_DIR/.env — пароль базы и токен купола сгенерированы"
  echo "ОСТАЛОСЬ: вписать PROVOD_API_KEY"
fi

say "4. Ключи доступа"
install -d -m 700 /root/.ssh
touch /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

if [[ -n "${DEPLOY_PUBKEY:-}" ]]; then
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    if grep -qxF "$key" /root/.ssh/authorized_keys; then
      echo "уже добавлен: ${key##* }"
    else
      echo "$key" >> /root/.ssh/authorized_keys
      echo "добавлен: ${key##* }"
    fi
  done <<< "$DEPLOY_PUBKEY"
else
  echo "DEPLOY_PUBKEY не передан — ключ для Actions придётся добавить вручную"
fi

say "Готово. Осталось вписать ключ provod.ai:"
echo "  nano /opt/artai/.env      # строка PROVOD_API_KEY"
echo
echo "Токен купола для адреса /dome?token=... :"
grep '^DOME_TOKEN=' /opt/artai/.env
echo
echo "После этого достаточно запушить в main — деплой пойдёт сам."
