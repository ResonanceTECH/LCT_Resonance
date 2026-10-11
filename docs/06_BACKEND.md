# 06. Backend

Точка входа: `backend/app/main.py` (`uvicorn app.main:app`). Префикс API: `/api`.  
Стек: Python ≥3.12, FastAPI, SQLAlchemy 2 asyncio, Alembic, Pydantic Settings, Argon2, PyJWT, asyncpg/psycopg, httpx, Uvicorn. Управление зависимостями: `uv` (`backend/pyproject.toml`).

---

## 1. Структура модулей

```text
backend/app/
├── main.py
├── api/
│   ├── router.py          сборка роутеров
│   └── routes/            auth, candidates, employer, vacancies, offers,
│                          tests, taxonomy, health, engagement, candidate
├── core/                  config, security, deps, rate_limit, errors
├── models/                SQLAlchemy
├── schemas/               Pydantic DTO camelCase
├── services/              бизнес-логика (profiles, testing, talent_pool, offers, fsp, …)
├── integrations/
│   ├── fsp/               mock + real adapters, fixtures
│   ├── matching/          baseline + http matcher
│   └── email.py
├── db/                    session, engine
└── seed/                  демо-данные
```

---

## 2. Важные сервисы

| Модуль | Файлы | Назначение |
| ------ | ----- | ---------- |
| Auth | `services/auth.py`, `core/security.py` | register/login, JWT, refresh, verify email |
| Profiles | `services/profiles.py` | CRUD кандидата, completeness, visibility |
| Testing | `services/testing.py`, generators | сессии, scoring, cooldown |
| Talent Pool | `services/talent_pool.py` | фильтры + вызов matcher |
| Matching | `integrations/matching/` | BaselineMatcher / HttpMatcher |
| Offers | `services/offers.py` | create, accept, contacts unlock |
| FSP | `services/fsp.py`, `integrations/fsp/` | sync/link, consent |
| Passport | связанный сервис passport | публичный slug |
| Seed | `app/seed/` | идемпотентные демо-данные |

Зависимости ролей: `CurrentUser`, `CandidateUser`, `EmployerUser`, `EmployerOrAdmin`, `AdminUser` в `core/deps.py`.

---

## 3. Подключение к БД

- Async: `DATABASE_URL` → asyncpg
- Sync/Alembic: `DATABASE_URL_SYNC` или Neon `DATABASE_URL_UNPOOLED`
- Rewrites для Neon URL — в `core/config.py`

---

## 4. Логирование и ошибки

- JSON-логи приложения, уровень `LOG_LEVEL`
- Единый формат ошибки API: `message`, `code`, `details`, `requestId`
- Rate limit: login/register 5/min/IP; resend 1/min; offers 50/day; флаг `RATE_LIMIT_ENABLED`

---

## 5. Фоновые задачи

Отдельного Celery/RQ нет. Тяжёлая работа — синхронно в request (тест finish, match batch, FSP sync). Письма — SMTP при регистрации.

---

## 6. PDF

Отдельной серверной генерации PDF резюме/паспорта **нет**. Career Passport — HTML/публичная страница + QR на Frontend.

---

## 7. Интеграция с ML

```text
MATCHER_PROVIDER=baseline → BaselineMatcher (default)
MATCHER_PROVIDER=ml + ML_MATCHER_URL → POST /rank
ошибка → fallback BaselineMatcher
```

Формула совпадает: `0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions`.

---

## 8. Интеграция с ФСП

`FSP_PROVIDER=mock` (default) | `real`.  
Mock читает `integrations/fsp/fixtures/members.json` и `achievements.json`.

---

## 9. Admin API

Префикс `/api/admin/*`: overview, users, users/{id}/status, offers, vacancies, assessments, categories. Требует `AdminUser`.

---

## 10. Health

- `GET /api/health/live` — процесс
- `GET /api/health/ready` — БД + сведения о fsp/matcher

Swagger: `http://localhost:8000/api/docs` или через nginx `http://localhost:8080/api/docs`.  
OpenAPI JSON: `/api/openapi.json`.

Подробный контракт — `07_API_REFERENCE.md` и `Backend.md`.
