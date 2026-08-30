# Деплой

Push в `main` → GitHub Actions собирает Docker-образ, кладёт его в GHCR и по SSH
говорит серверу забрать новый образ. Сервер ничего не собирает: на нём нужен только Docker.

```
push в main
   ↓
build:  docker build (фронт внутри) → ghcr.io/fouregg/artaiproject:<sha> и :latest
   ↓
deploy: ssh root@159.194.206.14 → docker compose pull && up -d
   ↓
проверка http://159.194.206.14/api/health
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
| `DEPLOY_HOST` | `159.194.206.14` |
| `DEPLOY_USER` | `root` |
| `DEPLOY_SSH_KEY` | приватный ключ `/root/.ssh/artai_deploy` целиком, с обеими строками `-----BEGIN/END-----` |

```bash
gh secret set DEPLOY_HOST --body "159.194.206.14"
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
ssh root@159.194.206.14
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

Выпуск кодов доступа на боевом сервере:

```bash
docker compose exec app python -m scripts.create_codes --count 10000 --quiet
docker compose exec postgres psql -U artai -d artai -c \
  "select code from users where code is not null order by created_at desc limit 20;"
```

## Пока без HTTPS

Сейчас приложение слушает 80-й порт по IP. Это осознанный временный режим, но помните:
коды доступа и анкеты с персональными данными идут по открытому каналу. Когда появится
домен, схема такая — добавить перед приложением nginx с Let's Encrypt, порт приложения
убрать из публичного доступа (`ports: ["127.0.0.1:8000:8000"]`) и открыть 443. Фронтенд
сам переключит сокет купола на `wss://`, править код не нужно.
