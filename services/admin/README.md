# Admin Service

Админка на FastAPI с простым интерфейсом (Jinja2 + минимальный CSS/JS).

## Функции
- Просмотр пользователей и подписок.
- Поиск пользователей по `tg_id`/`username`.
- Редактирование баланса/реферального баланса/username.
- Редактирование подписки и инструкций.
- Удаление пользователя вместе с подпиской.

## Требования
- Python 3.12

## Переменные окружения
- `DATABASE_URL` (обязательно)
- `ADMIN_USER` (опционально, default `admin`)
- `ADMIN_PASS` (опционально, default `Admin112008`)

## Запуск

```bash
cd services/admin
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8001
```

Открыть в браузере: `http://localhost:8001/admin/users`.
