# Bot Service (Техническое описание)

Документ описывает работу Telegram-бота в `services/bot`: хендлеры, callbacks, сервисы и хранилище.

## Точка входа

Файл: `services/bot/app/main.py`

- `main()`
  - Загружает переменные окружения через `dotenv`.
  - Проверяет наличие `BOT_TOKEN`.
  - Выполняет preflight проверки (`run_preflight()`).
  - Применяет миграции (`init_db()`).
  - Запускает планировщик `AsyncIOScheduler` с задачей очистки подписок каждые 10 минут.
  - Регистрирует роутеры: `start`, `subscription`, `payments`.
  - Запускает polling через `Dispatcher.start_polling()`.

## Preflight проверки

Файл: `services/bot/app/preflight.py`

- `_check_db()`
  - Требует `DATABASE_URL`.
  - Делает короткое соединение и `SELECT 1`.
- `_check_redis()`
  - Берет `REDIS_URL` или дефолт `redis://localhost:6379/0`.
  - Делает `PING`. При ошибке дает диагностическое сообщение.
- `_check_xui()`
  - Создает `XuiClient` из env и выполняет логин.
- `run_preflight()`
  - Запускает проверки БД и Redis в thread, XUI в async контексте.

## Хендлеры и бизнес-логика

### Роутер `start`

Файл: `services/bot/app/handlers/start.py`

Сообщения:
- `start_handler(message)`
  - Триггер: `/start`.
  - Создает пользователя, читает referral payload, сохраняет реферера.
  - Отправляет `img/start.png` с главным меню.
- `tariffs_handler(message)`
  - Триггер: `/tariffs` или "Тарифы".
  - Отправляет карточку тарифа (изображение + inline кнопки).
- `help_handler(message)`
  - Триггер: `/help` или "Help".
  - Отправляет контакт поддержки.
- `balance_handler(message)`
  - Триггер: `/balance` или "Баланс".
  - Читает балансы и отправляет карточку баланса.
- `start_button_handler(message)`
  - Триггер: "Старт".
  - Повторяет поведение `/start`.
- `referral_handler(message)`
  - Триггер: `/ref` или "Пригласи друга".
  - Формирует реферальную ссылку, статистику и правила.
- `personal_cabinet_handler(message)`
  - Триггер: "Личный кабинет".
  - Отправляет `img/profile.png` (если есть) + статус подписки.
  - При неактивной подписке показывает кнопку "Купить".

Callback:
- `connect_tariff(callback)`
  - Триггер: `tariff:connect`.
  - Редактирует сообщение, показывает выбор страны.
- `trial_tariff(callback)`
  - Триггер: `tariff:trial`.
  - Сообщает, что пробный доступ будет позже.
- `choose_country(callback)`
  - Триггер: `country:*`.
  - Показывает оплату с баланса.
- `pay_handler(callback)`
  - Триггер: `pay:balance`.
  - Списывает 150 с баланса, создает клиента в XUI, сохраняет подписку.
  - Отправляет инструкцию со ссылкой на VPN.
- `balance_topup(callback)`
  - Триггер: `balance:topup`.
  - Сообщает, что пополнение временно недоступно.
- `balance_open(callback)`
  - Триггер: `balance:open`.
  - Редактирует карточку баланса.
- `back_to_cabinet(callback)`
  - Триггер: `back:cabinet`.
  - Возвращает в личный кабинет.
- `cabinet_buy(callback)`
  - Триггер: `cabinet:buy`.
  - Отправляет следующее сообщение с тарифами.
- `back_to_balance(callback)`
  - Триггер: `back:balance`.
  - Возвращает на карточку баланса.
- `back_to_tariffs(callback)`
  - Триггер: `back:tariffs`.
  - Возвращает карточку тарифа.
- `back_to_countries(callback)`
  - Триггер: `back:countries`.
  - Возвращает список стран.

Вспомогательные функции:
- `_tariffs_content()`
  - Возвращает `(image_path, text)` для карточки тарифа.
- `_extract_start_payload(text)`
  - Парсит `/start <payload>`.
- `_personal_cabinet_text(user)`
  - Возвращает `(text, is_active)` с статусом и инструкцией.
  - Если в XUI нет клиента, чистит локальную подписку.
- `_vpn_instructions(link)`
  - Форматирует инструкцию подключения.
- `_fetch_xui_subscription(user)`
  - Ищет клиента по email в XUI, возвращает `(available, link, end_at)`.
- `_email_for_user(user)`
  - Возвращает `@{username}` или `@tg_{id}`.
- `_normalize_dt(value)`
  - Делает `datetime` timezone-aware.

### Роутер `payments`

Файл: `services/bot/app/handlers/payments.py`

- `choose_plan(callback)`
  - Триггер: `plan:*`.
  - Сообщает, что планы отключены.
- `pay_balance_plan(callback)`
  - Триггер: `pay:balance:*`.
  - Сообщает, что планы через баланс отключены.
- `pay(callback)`
  - Триггер: `pay:stars:*` или `pay:crypto:*`.
  - Сообщает, что Stars/Crypto отключены.

### Роутер `subscription`

Файл: `services/bot/app/handlers/subscription.py`

- `subscription_handler(message)`
  - Триггер: `/subscription` или `/sub`.
  - Вызывает API и выводит статус подписки или конфиг.
  - Использует `img/sub.png` если есть.

## Клавиатуры

Файл: `services/bot/app/keyboards/menu.py`

- `main_menu_keyboard()`
  - Reply клавиатура с основной навигацией.
- `tariffs_keyboard()`
  - Inline: подключить + пробный доступ.
- `payments_keyboard()`
  - Inline: оплата с баланса + назад.
- `balance_keyboard()`
  - Inline: назад в ЛК.
- `balance_payments_keyboard()`
  - Inline: назад.
- `personal_cabinet_keyboard(show_buy=False)`
  - Inline: опционально "Купить" + "Баланс".
- `countries_keyboard()`
  - Inline: Finland + назад.
- `plans_keyboard(plans)`
  - Inline: список планов (сейчас не используется).
- `payment_keyboard(plan_id)`
  - Inline: оплата плана с баланса (сейчас отключено).

## Сервисы

### XUI клиент

Файл: `services/bot/app/services/xui_client.py`

- `XuiConfig`
  - Поля: `base_url`, `base_path`, `sub_url`, `username`, `password`, `inbound_id`.
- `XuiClient.from_env()`
  - Требует `XUI_URL`, `XUI_USERNAME`, `XUI_PASSWORD`, `XUI_INBOUND_ID`.
  - Опционально: `XUI_SUB_URL`.
- `login()`
  - POST на endpoint логина XUI.
- `add_client(email, days=30)`
  - Создает клиента в XUI (перебирает несколько endpoint-путей).
  - Возвращает `sub_id`.
- `subscription_link(sub_id)`
  - Собирает публичную ссылку подписки.
- `get_client_subscription(email)`
  - Читает список inbound, ищет клиента по email.
  - Возвращает `(sub_id, end_at)` или `None`.
- `close()`
  - Закрывает HTTP клиент.

## Хранилище и кэш

Файл: `services/bot/app/storage.py`

БД:
- `_connect()`
  - Подключение к PostgreSQL через `DATABASE_URL`.
- `init_db()`
  - Запускает SQL-миграции из `services/bot/migrations`.
- `ensure_user(tg_id, username)`
  - Вставляет/обновляет пользователя.
- `set_referrer(tg_id, referrer_tg_id)`
  - Устанавливает реферера один раз.
- `get_referral_info(tg_id)`
  - Возвращает `ReferralInfo` и количество приглашенных.
- `record_first_payment(tg_id, amount)`
  - Фиксирует первую оплату и начисляет 50% рефереру.
- `transfer_referral_to_balance(tg_id, min_amount=150)`
  - Переносит реферальный баланс в основной.
- `deduct_balance(tg_id, amount)`
  - Списывает баланс пользователя.
- `set_subscription(tg_id, start_at, end_at, link, instructions)`
  - Апсерт подписки + запись в Redis.
- `get_subscription(tg_id)`
  - Возвращает `(start_at, end_at)`; чистит просроченные.
- `get_vpn_data(tg_id)`
  - Возвращает `(subscription_link, instructions)`.
- `clear_subscription(tg_id)`
  - Удаляет подписку из БД и кэша.
- `purge_expired_subscriptions()`
  - Удаляет все просроченные подписки.

Redis:
- `_redis()`
  - Клиент Redis на основе `REDIS_URL`.
- `_cache_key(tg_id)`
  - Формат ключа: `subscription:{tg_id}`.
- `_cache_set_subscription(...)`
  - Сохраняет подписку с TTL до `end_at`.
- `_cache_get_subscription(tg_id)`
  - Читает кэш и валидирует дату.
- `_cache_clear_subscription(tg_id)`
  - Удаляет ключ кэша.
- `_normalize_dt(value)`
  - Нормализует даты к UTC.

## Миграции

- Alembic: `services/bot/alembic` (версионные миграции БД).

## Переменные окружения

Обязательные:
- `BOT_TOKEN`
- `DATABASE_URL`
- `XUI_URL`
- `XUI_USERNAME`
- `XUI_PASSWORD`
- `XUI_INBOUND_ID`

Опциональные:
- `XUI_SUB_URL`
- `REDIS_URL`

## Диаграммы потоков

HTML-схемы потоков: `services/bot/docs/flows.html`.

## Сценарии ошибок и поведение

- XUI недоступен на preflight
  - Бот не стартует, выбрасывает ошибку в `run_preflight()`.
- Redis недоступен на preflight
  - Бот не стартует, сообщение: "Redis unavailable...".
- DB недоступна на preflight
  - Бот не стартует, сообщение о `DATABASE_URL` или ошибке подключения.
- XUI недоступен во время оплаты
  - В `pay_handler` ловится `httpx.TimeoutException`, пользователю отправляется сообщение о временной недоступности.
- Клиент удален в XUI
  - `_personal_cabinet_text` видит отсутствие клиента и вызывает `clear_subscription`, отображает "Подписка не активна".
- Истекла подписка по дате
  - `get_subscription` / `get_vpn_data` удаляют запись и возвращают отсутствие подписки.

## Чек-лист запуска

1) Запустить PostgreSQL и проверить `DATABASE_URL`.
2) Запустить Redis (`redis-cli ping` -> `PONG`).
3) Убедиться, что XUI доступен по `XUI_URL` и креды корректны.
4) Установить зависимости бота:

```bash
cd services/bot
pip install -r requirements.txt
```

5) Применить миграции:

```bash
python -m alembic -c alembic.ini upgrade head
```

Бот также запускает `alembic upgrade head` при старте через `init_db()`.

6) Запустить бота:

```bash
PYTHONPATH=. python -m app.main
```
