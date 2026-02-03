# VPN Telegram Bot

MVP реализация Telegram‑бота для продажи VPN‑доступа (Xray) с оплатами через Telegram Stars и CryptoBot, FastAPI‑бэкендом и простой админ‑панелью.

## Сервисы
- `bot` — aiogram, диалоги, оплата, выдача конфигов
- `admin` — админ‑панель управления пользователями (запускается отдельно, не в Docker)
- `db` — PostgreSQL
- `redis` — кэш подписок и уведомления

## Требования
- Python 3.12

Если используешь pyenv, файл `.python-version` уже задан.

## Быстрый запуск
1. Скопируйте `.env.example` в `.env` и заполните значения.
   - Для Docker используйте `DATABASE_URL` с хостом `db`.
2. Запустите docker compose:

```bash
docker compose -f docker/docker-compose.yml up --build -d
```

## Docker команды для прода

```bash
# Сборка образов
docker compose -f docker/docker-compose.yml build

# Запуск в фоне
docker compose -f docker/docker-compose.yml up -d

# Проверка статусов
docker compose -f docker/docker-compose.yml ps

# Логи бота
docker compose -f docker/docker-compose.yml logs -f bot

# Остановка
docker compose -f docker/docker-compose.yml down
```

## Локальный запуск (без Docker)
Для локального запуска используйте Python 3.12.
1. Создайте `.env` в корне проекта.
2. Для локального запуска установите `DATABASE_URL` на `postgresql://user:pass@localhost:5432/dbname`.
3. Установите зависимости отдельно для каждого сервиса.
4. Запустите сервисы в отдельных терминалах.

```bash
# Bot
cd services/bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python -m app.main
```

```bash
# Admin
cd services/admin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8001
```

## Админ‑панель
Открывайте `http://localhost:8001/admin/users`.

## Запуск бота и админки вместе

```bash
./scripts/run_all.sh
```

## Переменные окружения
- `DATABASE_URL`
- `BOT_TOKEN`
- `CRYPTOBOT_TOKEN`
- `PAYMENTS_ENABLED`
- `REDIS_URL`

## Примечания
- Оплаты по Stars и CryptoBot требуют настройки вебхуков (в текущей версии отключены).
