# Resonance Backend

FastAPI API для LCT Resonance. Префикс: **`/api`**. Контракт повторяет фронтенд один в один:
пути — `frontend/src/shared/api/endpoints.ts`, типы — `frontend/src/entities/types.ts`
(JSON в camelCase), поведение — `frontend/src/mocks/handlers.ts` (требование `Backend.md`).

Общий гайд FE+BE (запуск, карта API, happy path): **[`../README.md`](../README.md)**.

---

## Стек

| Слой | Технология |
|------|------------|
| HTTP | FastAPI, Uvicorn |
| DB | PostgreSQL 16, SQLAlchemy 2 (async), Alembic |
| Auth | JWT access 8 ч (+ refresh-cookie для `/api/auth/refresh`), RBAC |
| Password | Argon2id (вне event loop) |
| Integrations | `FSPAdapter` (mock/real), `Matcher` (baseline / ML по HTTP с fallback), SMTP |
| Settings | pydantic-settings ← локальный `.env` |
| Tooling | `uv`, pytest |

---

## Быстрый старт

### Локально (уже есть Postgres)

```bash
cd backend
cp .env.example .env   # заполните DATABASE_URL*, JWT_SECRET
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
```

| URL | Зачем |
|-----|--------|
| http://localhost:8000/api/docs | Swagger |
| http://localhost:8000/api/openapi.json | OpenAPI |
| `GET /api/health/live` | процесс жив |
| `GET /api/health/ready` | готовность (503, если БД недоступна) |

Фронт: `cd ../frontend && npm run dev` — Vite проксирует `/api` на `:8000`.

### Docker (из корня репо)

```bash
# нужен POSTGRES_PASSWORD в окружении или в корневом .env, и backend/.env (JWT_SECRET)
docker compose up -d --build
```

| URL | Что |
|-----|-----|
| http://localhost:8080 | UI (nginx) + прокси `/api` на backend, Swagger — `/api/docs` |
| http://localhost:8025 | Mailpit: письма подтверждения почты |
| http://localhost:8000 | backend напрямую |

- Миграции применяются при каждом старте контейнера, демо-сиды — при `SEED_ON_START=true`
  (по умолчанию; оба шага идемпотентны).
- В compose `APP_ENV=prod`: токен подтверждения не отдаётся в ответе, письмо уходит в Mailpit.
  Для жюри задайте `SMTP_*` настоящего сервера в корневом `.env` — значения compose перекрывают
  `backend/.env`. На публичном стенде нужен HTTPS: refresh-cookie помечен `Secure`.
- Если жюри смотрит стенд с одного NAT-адреса, лимиты на логин могут мешать: `RATE_LIMIT_ENABLED=false`.

---

## Config

Секреты только в локальном `.env` (gitignore). Шаблон со всеми ключами: [`.env.example`](./.env.example).

> На публичном стенде обязательно `APP_ENV=prod`: в `dev` регистрация отдаёт токен подтверждения
> в заголовке `X-Verification-Token` (обход почты для тестов), а refresh-cookie без `Secure`.

| Ключ | Назначение |
|------|------------|
| `DATABASE_URL` / `DATABASE_URL_SYNC` | async (`postgresql+asyncpg://…`) / Alembic (`postgresql+psycopg://…`) |
| `JWT_SECRET` | ≥32 символов |
| `JWT_ACCESS_TTL_MIN` / `JWT_REFRESH_TTL_DAYS` | 480 (у фронта нет refresh) / 7 |
| `CORS_ORIGINS` | CSV origins; не нужен, если фронт идёт через прокси `/api` |
| `PUBLIC_API_URL` / `PUBLIC_APP_URL` | база ссылки подтверждения email / ссылок Career Passport |
| `SMTP_*` | отправка писем; без `SMTP_HOST` в dev письмо не уходит, ссылка подтверждения пишется в лог (`email_not_sent`), вне dev регистрация отвечает 503. Настройка почты — [`SETUP.md`](../SETUP.md#почта) |
| `FSP_PROVIDER` | `mock` \| `real` |
| `MATCHER_PROVIDER` / `ML_MATCHER_URL` / `ML_TIMEOUT_SEC` | `baseline` \| `ml`; при ошибке ML — fallback на baseline |
| `PASS_SCORE` / `GRADE_COOLDOWN_DAYS` / `TEST_ATTEMPT_TTL_MIN` | порог теста / смена категории / время на тест |
| `TEST_RETRY_COOLDOWN_HOURS` | пауза перед пересдачей того же/более высокого грейда после провала |
| `STATIC_ITEM_MAX_EXPOSURES` | после стольких показов статический вопрос выходит из оборота |
| `CONSENT_VERSION` | версия текста согласий |
| `RATE_LIMIT_ENABLED` | лимиты на логин/регистрацию/письма/офферы |
| `LOG_LEVEL` | уровень JSON-логов `app.*` |

Спецсимволы в пароле БД в URL — percent-encode (`!` → `%21`).

---

## Seed (демо для FE и ручных проверок)

```bash
uv run python -m app.seed   # повторно → SEED_SKIP already seeded
```

Пароль всех демо-аккаунтов — `demo1234` (как в MSW-фикстурах фронта, только для демо-стенда).

| Роль | Email | Что показывает |
|------|-------|----------------|
| admin | `admin@demo.ru` | Админ Resonance |
| employer | `employer@demo.ru` | Игорь Смирнов, Resonance Labs: вакансии, шорт-лист, офферы во всех статусах |
| employer | `employer2@demo.ru` | Ольга Петрова, ТехноСфера: есть отклик кандидата |
| candidate | `candidate@demo.ru` | Анна Ковалёва, Frontend middle, тест 82, ФСП, входящий оффер |
| candidate | `elena@demo.ru` | Frontend middle, тест 91, без ФСП, office |
| candidate | `maxim@demo.ru`, `denis@demo.ru`, `sofia@demo.ru` | Backend middle, разные сигналы |
| candidate | `candidate1..8@demo.ru` | фон для поиска; без ФСП, часть без теста |

Демо-пара для защиты: на вакансии «Frontend Engineer (React)» Анна (тест 82) стоит **выше** Елены
(тест 91) — ранжирование учитывает стек, ФСП и условия, а не одно число; у Елены видны причины-минусы.

Также: 7 специализаций и 5 грейдов (как `labels.ts` фронта), 30 навыков, банк вопросов
(`app/seed/questions.py`), достижения ФСП из mock-реестра, согласия, уведомления, завершённые
тесты. Генерация детерминирована (фиксированный seed RNG).

---

## Архитектура `app/`

```
app/
├── main.py              # FastAPI, /api, request_id, access-лог, обработчики ошибок
├── api/routes/          # тонкие HTTP-handlers: deps + вызов сервиса
├── services/            # бизнес-логика: auth, candidate, profiles, talent_pool, matching,
│                        #   vacancies, vacancy_parser, offers, testing + question_generators,
│                        #   fsp, consents, notifications, shortlist, dashboards, insights,
│                        #   admin, companies, taxonomy, audit
├── models/              # ORM (индексы объявлены и в моделях — `alembic check` чистый)
├── schemas/             # DTO = типы фронта (camelCase через ApiModel)
├── integrations/
│   ├── fsp/             # FSPAdapter: MockFSPAdapter / RealFSPAdapter
│   ├── matching/        # Matcher: BaselineMatcher / HttpMatcher (ML)
│   └── email.py         # SMTP
├── db/                  # engine, session, Base
├── core/                # config, security, deps (роли), errors, logging, rate_limit
└── seed/                # демо-данные: data.py, questions.py, __main__.py
```

Правила:

- Handlers не содержат логики — только deps (`CandidateUser`, `EmployerUser`, `EmployerOrAdmin`, `AdminUser`) + service.
- Сервисы бросают `AppError(code, message, status)`; `message` — по-русски, его показывает UI.
- Справочники в API — как во фронте: специализация по имени (`Frontend`), грейд по коду
  (`middle`), навыки по названию с синонимами (`React.js` → `React`, неизвестный — создаётся).
- Match / тест / FSP / контакты — только на сервере. Без N+1: связи через `selectinload`,
  вычисляемые поля профиля (`testResult`, `fspSyncedAt`, заполненность) — пакетно.

---

## Ошибки

```json
{ "message": "Контакты доступны после принятия предложения", "code": "CONTACTS_LOCKED", "details": {}, "requestId": "req_…" }
```

Ошибки валидации: `422 VALIDATION_ERROR` (или `CURRENCY_NOT_SUPPORTED`, `INVALID_SALARY_RANGE`,
`SALARY_REQUIRED`), поля — в `details.fields[]` (`field`, `message`, `type`); введённые значения не
возвращаются. Заголовок ответа `X-Request-Id`.

---

## Ключевые правила API

### Auth

`POST /api/auth/register` → `{ accessToken, user }` сразу (как ждёт фронт) и письмо подтверждения.
Вход без подтверждённой почты разрешён, но работодатель не может отправлять офферы
(`403 EMAIL_NOT_VERIFIED`), а кандидат не виден в Talent Pool. `AuthUser` дополнен `emailVerified`.

### Talent Pool и матчинг (`GET /api/candidates`)

- Фильтры: `specialization`, `grade` (подтверждённый тестом), `skills` (через запятую, нужны все),
  `workFormat`, `readiness`, `salaryFrom/salaryTo` (пересечение вилок), `fspDiscipline`,
  `hasFspAchievements`, `q`, `sort` (`match|grade|salary|name`), `page`, `limit ≤ 50`.
- С `vacancyId`: жёсткий фильтр — подтверждённая категория вакансии и `readiness ≠ not_looking`;
  каждому элементу добавляется `match`, сортировка по score.
- `match.reasons[]` = `{ code, label, positive }` по словарю `Backend.md`; зарплата и формат
  не отсекают кандидата, а дают минус (`SALARY_MISMATCH`, `WORK_FORMAT_MISMATCH`).
- Формула baseline: `0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions`; разряд ФСП — бонус
  один раз. ML получает тот же контракт (`app/schemas/matcher_contract.py`, camelCase).

### Офферы и контакты

- `POST /api/offers`: зарплата в рублях обязательна, `vacancyId` необязателен, компания создаётся
  из `companyName`, `employerContact` по умолчанию — email работодателя. Один активный оффер
  кандидату на вакансию (`409 OFFER_ALREADY_EXISTS`).
- `GET /api/offers/{id}`: первое открытие кандидатом переводит `new` → `viewed`.
- `accept`/`decline` — атомарно, повтор → `409 INVALID_OFFER_STATE`; работодатель получает уведомление.
- `GET /api/candidates/{id}/contacts` — только после принятого оффера этого работодателя или
  отклика кандидата на его вакансию, иначе `403 CONTACTS_LOCKED`; раскрытие пишется в аудит.

### Тестирование (`/api/tests/sessions`)

- `POST` создаёт сессию из 10 вопросов по blueprint специализации; повторный старт того же теста
  возвращает открытую сессию (вопросы не «перекатываются»).
- Вопросы генерируются из шаблонов (`services/question_generators.py`: SQL, вывод Python,
  сложность, event loop и приведение типов в JS, батчинг `useState`) или берутся из банка.
  Каждый показ — новый экземпляр; генератор и seed хранятся в `test_attempt_items`.
- `GET …/question` отдаёт текущий вопрос с `code`, `index`, `total`; `POST …/answer` двигает
  `currentIndex`; `POST …/finish` считает результат (пропуски — неверно), проходной балл `PASS_SCORE`.
- Провал не понижает подтверждённый грейд и не затирает балл для ранжирования; тот же или более
  высокий грейд — после `TEST_RETRY_COOLDOWN_HOURS` (`409 TEST_RETRY_COOLDOWN`), ниже — сразу.

### ФСП и согласия

- Синхронизация и привязка требуют согласия `fsp_sync` (`403 CONSENT_REQUIRED`; фронт предлагает
  его дать). Без привязки участник ищется в реестре по email и ФИО; не найден — `200` с пустым списком.
- `status`: `synced` / `no_history` (норма, не ошибка) / `stale` (реестр недоступен, отдан кэш).
- Mock-реестр: `FSP-2026-00123`, `-00456`, `-00789` (с историей), `-00999` (без истории),
  `FSP-TIMEOUT` (недоступность), `-00555` — участник с email `candidate1@demo.ru` для автопривязки.
- `GET/PUT /api/candidates/me/consents`: `personal_data`, `profile_publication`, `fsp_sync`
  с версией и историей. Отзыв публикации скрывает профиль, отзыв ФСП удаляет данные ФСП.

### Лимиты

`429 RATE_LIMITED` + `Retry-After`: регистрация и логин — 5 в минуту с IP, повторное письмо —
1 в минуту, офферы — 50 в сутки на работодателя (в памяти процесса).

---

## Миграции и схема

```bash
uv run alembic upgrade head
uv run alembic check                              # модели и миграции не разошлись
uv run alembic revision --autogenerate -m "…"     # только осознанно
```

До первого релиза схема живёт в одной миграции `0001_initial_schema`; новые изменения — отдельными
ревизиями поверх неё. База, созданная до схлопывания миграций (в `alembic_version` старая
ревизия), не обновится: пересоздайте её (`docker compose down -v` или `DROP DATABASE` +
`CREATE DATABASE`), затем `alembic upgrade head && python -m app.seed`.

---

## Тесты

```bash
uv run pytest tests/unit -q          # без БД и без .env
uv run pytest tests/integration -q   # нужен мигрированный и засиженный Postgres
```

- `test_frontend_contract.py` читает `frontend/src/entities/types.ts` и проверяет, что ответы API
  содержат все обязательные поля типов фронта.
- `test_golden_path.py` — сквозной сценарий через API фронта; `test_seed_demo.py` — демо-данные.
- Генераторы вопросов сверяются с SQLite, интерпретатором Python и Node (если установлен).

Интеграционные тесты повторяемы, но оставляют данные — гоняйте их на отдельной базе.

---

## Секреты

- Никогда не коммитить `.env`.
- Не логировать password, tokens, phone, email, полные тела офферов/профилей, raw FSP PII.
- Demo seed-пароли допустимы в доках; боевые — нет.
