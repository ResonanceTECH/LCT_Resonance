# 13. Конфигурация окружения

Секреты только в локальных `.env` (gitignore). Шаблоны: корневой `.env` (Postgres для compose), `backend/.env.example`.

---

## 1. Корневой `.env` (Docker Compose)

| Переменная | Назначение | Обязательная | Пример локально | Где |
| ---------- | ---------- | ------------ | --------------- | --- |
| `POSTGRES_PASSWORD` | пароль БД | да для compose | `DemoPass123` | compose postgres + DATABASE_URL backend |
| `POSTGRES_USER` | пользователь | нет | `fspadmin` | compose |
| `POSTGRES_DB` | имя БД | нет | `fsphack` | compose |
| `APP_ENV` | режим backend в compose | нет | `prod` (default compose) | backend container |
| `PUBLIC_API_URL` | ссылки в письмах | нет | `http://localhost:8080` | backend |
| `PUBLIC_APP_URL` | ссылки приложения | нет | `http://localhost:8080` | backend |
| `CORS_ORIGINS` | CORS | нет | `http://localhost:8080` | backend |
| `SMTP_*` | почта | для prod писем | mailpit defaults в compose | backend |
| `SEED_ON_START` | сид при старте | нет | `true` | backend |
| `RATE_LIMIT_ENABLED` | лимиты | нет | `true` | backend |
| `MATCHER_PROVIDER` | baseline\|ml | нет | `baseline` | backend |
| `ML_MATCHER_URL` | URL ML | для ml | `http://ml:8001` | backend |
| `ML_TIMEOUT_SEC` | таймаут | нет | `2` | backend |
| `VITE_USE_MOCKS` | моки FE build | нет | `false` | frontend build-arg |

---

## 2. Backend `.env`

| Переменная | Назначение | Обязательная | Локальный пример | Где |
| ---------- | ---------- | ------------ | ---------------- | --- |
| `APP_ENV` | dev\|prod | нет | `dev` | config |
| `LOG_LEVEL` | логи | нет | `INFO` | config |
| `DATABASE_URL` | async DB | да | `postgresql+asyncpg://fspadmin:…@localhost:5432/fsphack` | SQLAlchemy |
| `DATABASE_URL_SYNC` | sync/Alembic | да* | `postgresql+psycopg://…` | Alembic |
| `DATABASE_URL_UNPOOLED` | Neon helper | нет | Neon direct | → sync |
| `JWT_SECRET` | подпись JWT | да ≥32 | `secrets.token_urlsafe(48)` | security |
| `JWT_ACCESS_TTL_MIN` | TTL access | нет | `480` | JWT |
| `JWT_REFRESH_TTL_DAYS` | TTL refresh | нет | `7` | sessions |
| `CORS_ORIGINS` | CSV origins | нет | `http://localhost:5173` | CORS |
| `PUBLIC_API_URL` | verify links | нет | `http://localhost:8000` | email/passport |
| `PUBLIC_APP_URL` | app links | нет | `http://localhost:5173` | email |
| `SMTP_HOST` | SMTP | prod да | пусто или `localhost` | email |
| `SMTP_PORT` | порт | нет | `1025` Mailpit / `587` | email |
| `SMTP_USERNAME` | auth | нет | | email |
| `SMTP_PASSWORD` | auth | нет | | email |
| `SMTP_FROM_EMAIL` | From | нет | `no-reply@resonance.local` | email |
| `SMTP_USE_SSL` | SSL | нет | `false` | email |
| `SMTP_STARTTLS` | STARTTLS | нет | `false` Mailpit / `true` prod | email |
| `FSP_PROVIDER` | mock\|real | нет | `mock` | FSP |
| `FSP_BASE_URL` | real API | для real | | RealFSPAdapter |
| `FSP_API_TOKEN` | Bearer | для real | | RealFSPAdapter |
| `FSP_TIMEOUT_SEC` | таймаут | нет | `2` | FSP |
| `FSP_CACHE_TTL_HOURS` | кеш | нет | `24` | FSP service |
| `MATCHER_PROVIDER` | baseline\|ml | нет | `baseline` | matching |
| `ML_MATCHER_URL` | ML HTTP | для ml | `http://localhost:8001` | HttpMatcher |
| `ML_TIMEOUT_SEC` | таймаут | нет | `2` | HttpMatcher |
| `PASS_SCORE` | порог теста | нет | `70` | testing |
| `GRADE_COOLDOWN_DAYS` | смена категории | нет | `90` | testing |
| `TEST_ATTEMPT_TTL_MIN` | TTL сессии | нет | `30` | testing |
| `TEST_RETRY_COOLDOWN_HOURS` | пауза пересдачи | нет | `24` | testing |
| `STATIC_ITEM_MAX_EXPOSURES` | ротация static | нет | `200` | testing |
| `CONSENT_VERSION` | версия текстов | нет | `2026-10-01` | consents |
| `RATE_LIMIT_ENABLED` | лимиты | нет | `true` | rate_limit |

\* Sync URL обязателен для миграций; может выводиться из UNPOOLED.

---

## 3. Frontend env

| Переменная | Назначение | Обязательная | Пример | Где |
| ---------- | ---------- | ------------ | ------ | --- |
| `VITE_USE_MOCKS` | MSW | нет | `true` / `false` | `src/shared/config/env.ts` |
| `VITE_API_BASE_URL` | base path API | нет | `/api` | env.ts, Dockerfile |
| `VITE_API_PROXY_TARGET` | proxy target Vite | нет | `http://localhost:8000` | vite.config.ts |

---

## 4. Безопасный `.env.example`

Актуальный шаблон Backend уже лежит в `backend/.env.example`. Не коммитьте заполненный `.env`. Для жюри на одном NAT при демо можно временно `RATE_LIMIT_ENABLED=false`.
