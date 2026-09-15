# NYX VPN Bot

Telegram-бот для продажи VPN-доступа (Xray / 3x-ui) с веб-кабинетом и админ-панелью. Два сервиса делят одну БД и Redis: `bot` (aiogram, Telegram-диалоги и выдача конфигов) и `admin` (FastAPI — админка + публичный личный кабинет). Инфраструктура — Postgres 16 и Redis 7.

## Архитектура

```
docker/
  docker-compose.yml   # db, redis, bot, admin, nginx (80/443)
  nginx/nginx.conf     # reverse-proxy поддомена кабинета → admin:8001
  scripts/issue_cert.sh# выпуск TLS (certbot/Let's Encrypt, webroot)
  certbot/             # исключено из git: conf/ и www/ с .pem/.key

services/
  bot/                 # aiogram 3.6, provision XUI, APScheduler-уведомления, JWT-кабинет
    app/
      main.py          # preflight(DB/Redis/XUI) → Alembic → scheduler → polling
      handlers/        # Telegram-диалоги и команды бота
      services/xui_client.py
      storage.py       # Postgres + кэш Redis subscription:{tg_id}
      sync_panel.py    # разовый импорт панель → БД (dry-run / --apply)
      utils/           # вспомогательные интеграции
    alembic/ alembic.ini

  admin/               # FastAPI + Jinja2 + uvicorn :8001
    app/
      main.py          # /admin/* — HTTP Basic; /cabinet — JWT (публичный)
      routes/{users,subscriptions,cabinet}.py
      templates/cabinet.html  # самодостаточная страница (тёмная тема, glassmorphism)
      static/ db.py config.py
    Dockerfile         # python:3.12-slim, CMD uvicorn 0.0.0.0:8001

scripts/run_all.sh     # локальный запуск bot + admin рядом
```

Общий Postgres: таблицы `users` и `subscriptions` (см. `services/bot/alembic/versions/`). Redis хранит только актуальные подписки `subscription:{tg_id}` с TTL=`end_at`.

## Требования

- Python 3.12, Docker Engine + Compose v2, `pyenv` опционально (`.python-version` задан).
- Домен с A-записью поддомена кабинета → IP сервера (для `docker/nginx/nginx.conf` и certbot).

## Быстрый старт

### 1. Окружение

```bash
cp .env.example .env
# заполни .env (см. «Переменные окружения»); в Docker DATABASE_URL/REDIS_URL на хосты db/redis
```

### 2. Запуск через Docker (рекомендуемый путь)

```bash
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f bot     # логи бота
docker compose -f docker/docker-compose.yml logs -f admin   # логи кабинета/админки
docker compose -f docker/docker-compose.yml logs -f nginx
docker compose -f docker/docker-compose.yml down            # остановить стек
```

Внутри Docker доступна только `db:5432`/`redis:6379` и `admin` через `expose 8001` → наружу торчит лишь `nginx` на `80`/`443`.

### 3. TLS для поддомена кабинета

`docker/nginx/nginx.conf` по умолчанию обслуживает `cab.nyxvps.space` — замени на свой поддомен где стоит A-запись, пересобери/перезапусти `nginx`. Сертификаты кладутся в `docker/certbot/conf` (в `.gitignore`, не коммить `.pem/.key`).

```bash
# после `docker compose up -d` (нужен nginx на :80 для HTTP-01)
DOMAIN=cab.example.com EMAIL=admin@example.com bash docker/scripts/issue_cert.sh
# или вручную docker run certbot/certbot ... --webroot -w /var/www/certbot -d <домен>

# продление
docker run --rm -v ./docker/certbot/www:/var/www/certbot -v ./docker/certbot/conf:/etc/letsencrypt \
  certbot/certbot renew
docker compose -f docker/docker-compose.yml restart nginx
```

`CABINET_URL` в `.env` должен совпадать с этим поддоменом: `https://cab.example.com` (без слэша).

### 4. Локальный запуск без Docker

```bash
# Postgres/Redis подними любым способом и поправь DATABASE_URL на localhost

# Bot
cd services/bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m app.main

# Admin (в другом терминале) — http://localhost:8001/admin/users
cd services/admin
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8001
```

Или оба разом:

```bash
./scripts/run_all.sh
```

## Команды

### Docker

```bash
docker compose -f docker/docker-compose.yml build              # пересобрать образы
docker compose -f docker/docker-compose.yml up -d              # поднять
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f --tail 200 bot
docker compose -f docker/docker-compose.yml exec bot python -m app.sync_panel              # dry-run панель→БД
docker compose -f docker/docker-compose.yml exec bot python -m app.sync_panel --apply      # запись в БД
docker compose -f docker/docker-compose.yml exec bot python -m app.broadcast "текст"        # рассылка
docker compose -f docker/docker-compose.yml down
```

### Миграции (Alembic в services/bot)

Бот сам накатывает `alembic upgrade head` на старте (`init_db()`). Вручную:

```bash
cd services/bot
python -m alembic -c alembic.ini upgrade head
python -m alembic -c alembic.ini current
```

### Панель → БД (одноразовый импорт)

```bash
# сухой прогон — таблицу в консоль, БД не трогает
python -m app.sync_panel                    # локально (PYTHONPATH=. из services/bot)
docker compose -f docker/docker-compose.yml exec bot python -m app.sync_panel

# запись в БД после сверки dry-run
python -m app.sync_panel --apply
docker compose -f docker/docker-compose.yml exec bot python -m app.sync_panel --apply
```

Пишутся только резолвимые `email`: `@tg_{id}` напрямую и `@username` через Telegram `getChat`; без `@`/сервис-имена/нерезолвимые — в skip-отчёт, не пишутся.

## Переменные окружения (`.env` / `.env.example`)

| Переменная | Назначение |
|---|---|
| `BOT_TOKEN`, `BOT_USERNAME` | Токен бота и `@username` (deep-link кнопок кабинета) |
| `DATABASE_URL`, `POSTGRES_*` | DSN Postgres; в Docker — хост `db`, локально `localhost` |
| `REDIS_URL` | `redis://redis:6379/0` в Docker, `redis://localhost:6379/0` локально |
| `ADMIN_USER`, `ADMIN_PASS`, `ADMIN_ID` | Basic-авторизация админки и Telegram-id админа |
| `XUI_URL`, `XUI_USERNAME`, `XUI_PASSWORD`, `XUI_INBOUND_IDS`, `XUI_SUB_URL` | Панель 3x-ui и inbounds |
| `JWT_SECRET`, `CABINET_URL` | Подпись ссылок кабинета (`https://cab.example.com` на проде) |
| `TRIAL_DAYS`, `REMIND_HOURS_BEFORE`, `SUBSCRIPTION_PURGE_GRACE_HOURS` | Сроки пробника/напоминаний/чистки |
| Прочие ключи из `.env.example` | См. файл — значения для внешних интеграций |

Бот не стартует без `BOT_TOKEN`; preflight перед всем остальным жёстко проверяет доступность DB/Redis/XUI и прерывает запуск при сбое.

## Админка и кабинет

- Админка: `https://<поддомен>/admin/users` (и `/admin/subscriptions`), HTTP Basic (`ADMIN_USER`/`ADMIN_PASS`), через nginx.
- Кабинет: `https://<поддомен>/cabinet?t=<jwt>` — публичный, JWT `HS256` на 1 час (выдаёт бот по кнопке «Личный кабинет»), данные тянет `GET /cabinet/api/subscription?t=`.

## Примечания

- `docker/certbot/**` и любые `*.pem/*.key/*.crt` — в `.gitignore` вместе с `.env`; не коммитить.
- В этой версии бот и проверка окружения не требуют публичной регистрации вебхуков.
