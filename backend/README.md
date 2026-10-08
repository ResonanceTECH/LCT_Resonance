# Resonance Backend

FastAPI API для LCT Resonance. Префикс: **`/api/v1`**.

Общий гайд FE+BE (интеграция, расхождения с MSW, happy path): **[`../README.md`](../README.md)**.  
Бэклог и решения: [`TASKS.md`](./TASKS.md).

---

## Стек

| Слой | Технология |
|------|------------|
| HTTP | FastAPI, Uvicorn |
| DB | PostgreSQL 16, SQLAlchemy 2 (async), Alembic |
| Auth | JWT access + refresh session (HttpOnly cookie) |
| Password | Argon2id |
| Integrations | `FSPAdapter` (mock/real), `BaselineMatcher` (+ опциональный ML HTTP) |
| Settings | pydantic-settings ← локальный `.env` |
| Tooling | `uv`, pytest |

---

## Быстрый старт

### Локально (уже есть Postgres)

```bash
cd backend
# создайте .env (см. раздел Config) — не коммитьте
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
```

| URL | Зачем |
|-----|--------|
| http://localhost:8000/docs | Swagger |
| http://localhost:8000/openapi.json | OpenAPI |
| `GET /health/live` | процесс жив |
| `GET /health/ready` | готовность (в т.ч. БД) |

### Docker (из корня репо)

```bash
# нужен POSTGRES_PASSWORD в окружении / корневом env для compose
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Compose поднимает `postgres` + `backend`, пробрасывает `:5432` и `:8000`.

---

## Config

Секреты только в локальном `.env` (gitignore). Не дублируйте пароли в markdown.

Ожидаемые ключи (имена):

| Ключ | Назначение |
|------|------------|
| `DATABASE_URL` | async SQLAlchemy (`postgresql+asyncpg://…`) |
| `DATABASE_URL_SYNC` | Alembic / sync (`postgresql+psycopg://…`) |
| `JWT_SECRET` | ≥32 символов |
| `JWT_ACCESS_TTL_MIN` / `JWT_REFRESH_TTL_DAYS` | TTL |
| `CORS_ORIGINS` | CSV origins (нужен `http://localhost:5173` для Vite) |
| `FSP_PROVIDER` | `mock` \| `real` |
| `MATCHER_PROVIDER` | `baseline` (ML URL опционален) |
| `PASS_SCORE` / `GRADE_COOLDOWN_DAYS` | порог теста / cooldown |

Спецсимволы в пароле БД в URL — percent-encode (`!` → `%21`).

Загрузка: `app/core/config.py` → файл `backend/.env`.

---

## Seed (демо для FE и ручных проверок)

```bash
uv run python -m app.seed
# повторно → SEED_SKIP already seeded
```

| Роль | Email | Пароль |
|------|-------|--------|
| admin | `admin@example.invalid` | `AdminPass123!` |
| employer | `employer1@example.invalid` | `EmployerPass123!` |
| candidate A (с FSP) | `candidate.a@example.invalid` | `CandidatePass123!` |
| candidate B | `candidate.b@example.invalid` | `CandidatePass123!` |

Также: 2 employer + компании, 5 vacancies, ~10 доп. кандидатов, taxonomy (skills/grades/specs), тестовые вопросы, sample offers в разных статусах.

---

## Архитектура `app/`

```
app/
├── main.py              # FastAPI, CORS, request_id, routers
├── api/v1/              # тонкие HTTP-handlers
├── services/            # бизнес-логика
├── models/              # ORM
├── schemas/             # request/response DTO
├── integrations/
│   ├── fsp/             # MockFSPAdapter / RealFSPAdapter
│   └── matching/        # BaselineMatcher
├── db/                  # engine, session, Base
├── core/                # config, security, deps, errors
└── seed/                # демо-данные
```

Правила:

- Handlers не содержат тяжёлой логики — только deps + service.  
- Match / FSP / grade verification — в services/integrations, не на клиенте.  
- Contacts кандидата наружу — только через offer flow после `accepted`.

---

## Auth (для фронта)

1. `POST /api/v1/auth/register` → может потребовать verify (`verification_token` только в `APP_ENV=dev`).  
2. `POST /api/v1/auth/login` →  
   - JSON: `{ "access_token", "token_type", "expires_in" }`  
   - Set-Cookie: `refresh_token` (HttpOnly, `path=/api/v1/auth`)  
3. Дальше: `Authorization: Bearer <access_token>`.  
4. `POST /api/v1/auth/refresh` — по cookie, без тела.  
5. `GET /api/v1/auth/me` → `{ id, email, role, email_verified }`.  

Роли: `candidate` | `employer` | `admin` (`require_roles` в deps).

> FE MSW сейчас отдаёт `{ accessToken, user }` и не использует refresh/verify — см. таблицу расхождений в корневом README §5.3.

---

## HTTP API (кратко)

База: `/api/v1`. Полные схемы — Swagger.

### Ошибки

```json
{
  "error": {
    "code": "SOME_CODE",
    "message": "…",
    "details": {},
    "request_id": "req_…"
  }
}
```

Заголовок ответа: `X-Request-Id`.

### Группы роутов

| Prefix | Файл | Суть |
|--------|------|------|
| `/auth` | `auth.py` | register, verify, login, refresh, logout, me |
| `/specializations`, `/grades`, `/skills` | `taxonomy.py` | справочники |
| `/candidates` | `candidates.py` | профиль, FSP, список, public card |
| `/tests` | `tests.py` | attempts / submit |
| `/companies` | `companies.py` | CRUD компаний |
| `/vacancies`, `/companies/me/vacancies` | `vacancies.py` | CRUD + publish/close |
| `/matching` | `matching.py` | `POST /search` |
| `/offers` | `offers.py` | create, view, accept, **reject**, withdraw, candidate-contact |
| `/health/*` | `health.py` | без префикса v1 |

### Matching (вместо FE `GET /candidates?vacancyId=`)

```http
POST /api/v1/matching/search
```

Тело (кратко): `vacancy_id` и/или `need` + `limit`/`offset`.  
Ответ: `items[{ candidate, match }]`, `total`, `matcher`.

### Offers / contacts

- Отклонение: **`POST /offers/{id}/reject`** (не `/decline`).  
- Контакты: **`GET /offers/{id}/candidate-contact`** после accept (не `/candidates/{id}/contacts`).

### Testing

- Старт: `POST /tests/attempts`  
- Сдача: `POST /tests/attempts/{id}/submit`  
Правильные ответы клиенту до submit не отдаются.

---

## Что важно фронту при подключении

1. Prefix **`/api/v1`**, не `/api`.  
2. Парсить `error.message` / `error.code`.  
3. Talent Pool → `POST /matching/search`.  
4. ID — UUID, не `cand-1`.  
5. Сначала company, потом vacancy.  
6. CORS: origin Vite в `CORS_ORIGINS`, credentials если работаете с refresh-cookie.  
7. Не считать score на клиенте; не показывать контакты без успешного contact endpoint.

Чеклист интеграции и happy path — в [`../README.md`](../README.md).

---

## Миграции и схема

```bash
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "…"   # только осознанно
```

Стартовая ревизия: `alembic/versions/e54cfea96046_initial_schema.py`.

Если DBeaver показывает пустой `public` — миграции не применены.  
Если `password authentication failed` — пароль роли Postgres ≠ URL в `.env`.

---

## Тесты

```bash
uv run pytest tests/unit -q
# integration / golden path — нужен рабочий DATABASE_URL
uv run pytest tests/integration -q
```

---

## Скрипты

| Команда | Что |
|---------|-----|
| `uv sync` | зависимости |
| `uv run alembic upgrade head` | схема |
| `uv run python -m app.seed` | демо-данные |
| `uv run uvicorn app.main:app --reload --port 8000` | API |
| `uv run pytest …` | тесты |

---

## Секреты

- Никогда не коммитить `.env`.  
- Не логировать password, tokens, phone, email, полные тела офферов/профилей, raw FSP PII (`TASKS.md`).  
- Demo seed-пароли допустимы в доках; боевые — нет.

---

*Источник правды по HTTP — OpenAPI `/docs`. При расхождении с FE MSW правим клиент под бэкенд (или явно версионируем адаптер), не переносим MSW-формулы в prod UI.*
