# Деплой

Push в `main` → GitHub Actions собирает Docker-образ, кладёт его в GHCR и по SSH
говорит серверу забрать новый образ. Сервер ничего не собирает: на нём нужен только Docker.

```
push в main
   ↓
build:  docker build (фронт внутри) → ghcr.io/fouregg/artaiproject:<sha> и :latest
   ↓
deploy: ssh root@ai.tavrida.art → docker compose pull && up -d
   ↓
проверка https://ai.tavrida.art/api/health
```

## Первичная настройка сервера

Один раз, от root на сервере. `DEPLOY_PUBKEY` — публичный ключ, приватная часть
которого лежит в секрете `DEPLOY_SSH_KEY`:

```bash
DEPLOY_PUBKEY='ssh-ed25519 AAAA... github-actions-artai-deploy' \
  bash <(curl -fsSL https://raw.githubusercontent.com/fouregg/ARTAIProject/main/deploy/bootstrap.sh)
```

Скрипт ставит Docker, создаёт `/opt/artai` с `docker-compose.yml`, генерирует `.env`
(пароль базы и токен купола — случайные) и прописывает ключ в `authorized_keys`.
Повторный запуск безопасен: `.env` не перезаписывается, ключи не дублируются.

После него остаётся вписать ключ provod.ai:

```bash
nano /opt/artai/.env      # PROVOD_API_KEY=sk_...
```

## Секреты репозитория

| Секрет | Значение |
|---|---|
| `DEPLOY_HOST` | `ai.tavrida.art` |
| `DEPLOY_USER` | `root` |
| `DEPLOY_SSH_KEY` | приватный ключ `/root/.ssh/artai_deploy` целиком, с обеими строками `-----BEGIN/END-----` |

```bash
gh secret set DEPLOY_HOST --body "ai.tavrida.art"
gh secret set DEPLOY_USER --body "root"
gh secret set DEPLOY_SSH_KEY < artai_deploy
```

`GITHUB_TOKEN` создавать не нужно — он выдаётся самим Actions и используется, чтобы
залогиниться в GHCR на сервере на время выкатки. После деплоя `docker logout` убирает его.

## Что происходит с данными

- **База** — том `pgdata`, переживает передеплой. Миграции применяются при старте
  приложения (`AUTO_MIGRATE=true`), отдельного шага нет.
- **Картинки** — том `storage`, тоже переживает передеплой.
- **`.env`** на сервере деплой не трогает, только дописывает строку `APP_IMAGE`
  с выкаченным тегом.

## Откат

```bash
ssh root@ai.tavrida.art
cd /opt/artai
docker compose images app                       # какой тег сейчас
sed -i 's|^APP_IMAGE=.*|APP_IMAGE=ghcr.io/fouregg/artaiproject:<нужный-sha>|' .env
docker compose up -d
```

Теги живут в GHCR по короткому SHA коммита, так что откатиться можно на любой прошлый деплой.

## Полезное на сервере

```bash
cd /opt/artai
docker compose ps                      # что запущено
docker compose logs -f app --tail 100  # логи приложения
docker compose exec postgres psql -U artai -d artai   # база
docker compose restart app
```

## HTTPS

Наружу смотрит nginx (`deploy/nginx.conf`), приложение публичного порта не имеет —
только внутренняя сеть compose. С 80-го идёт редирект на 443, кроме пути проверки
Let's Encrypt. Сокет цифрового холста проксируется с апгрейдом, таймаут чтения час:
экран висит на связи сутками, а генерация занимает до полутора минут.

Сертификат выпущен на `ai.tavrida.art`. Контейнер `certbot` дважды в сутки пробует
продлить его методом webroot; Let's Encrypt обновляет за месяц до конца срока.

```bash
# что с сертификатом
docker compose run --rm --entrypoint certbot certbot certificates

# продлить вручную и перечитать конфиг
docker compose run --rm --entrypoint certbot certbot renew --webroot -w /var/www/certbot
docker compose exec nginx nginx -s reload
```

Первый выпуск делался в режиме standalone при остановленном приложении — 80-й порт
должен быть свободен. Продление так не работает: оно идёт через nginx и простоя не требует.
