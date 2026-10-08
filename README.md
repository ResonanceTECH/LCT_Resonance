# LCT Resonance

Веб-сервис **обратного рекрутинга**: работодатель ищет кандидатов (Talent Pool + Match Score + ФСП), кандидат получает офферы и принимает/отклоняет. Контакты кандидата открываются **только после Accept**, на стороне Backend.

Спец.трек хакатона. Репозиторий — monorepo:


| Папка                            | Стек                                     | Порт (dev)       | Документация                                                                                                                 |
| -------------------------------- | ---------------------------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `[frontend/](./frontend/)`       | React 19, Vite, TanStack Query, MSW      | `:5173`          | `[frontend/README.md](./frontend/README.md)`, `[TECH_SPEC.md](./frontend/TECH_SPEC.md)`, `[UI_KIT.md](./frontend/UI_KIT.md)` |
| `[backend/](./backend/)`         | FastAPI, SQLAlchemy, Alembic, PostgreSQL | `:8000`          | `[backend/README.md](./backend/README.md)`, `[TASKS.md](./backend/TASKS.md)`                                                 |
| `[compose.yaml](./compose.yaml)` | Postgres (+ backend image)               | `:5432`, `:8000` | ниже                                                                                                                         |


**Этот файл** — общий гайд для фронта и бэка: как поднять, кто за что отвечает, контракт API и где сейчас расхождения FE-mocks ↔ BE.

---

## 1. Продуктовые границы (обязательно читать обеим ролям)


| Делает Backend                                  | Делает Frontend                                      |
| ----------------------------------------------- | ---------------------------------------------------- |
| Auth (JWT + refresh cookie), RBAC               | UI логина/регистрации, хранение access token, guards |
| Match Score / ranking / Skill Radar (если есть) | Только отображение DTO                               |
| Результаты теста, правильные ответы             | Вопросы без `correct`, прогресс, UI результата       |
| FSP sync через адаптер                          | Кнопка sync, список достижений, Verified badge       |
| Раскрытие контактов после Accept                | Показ контактов **только** из успешного API          |
| Аудит, валидация бизнес-правил                  | Валидация форм (Zod), empty/loading/error            |


Анти-цели фронта: не считать match/test на клиенте; не ходить в ФСП напрямую; не «раскрывать» контакты по статусу оффера в обход API.

Поток:

```
Browser (React)  →  Backend /api/v1  →  Postgres
                         ↓
              FSP adapter / Matcher (baseline|ML)
```

Пока фронт на MSW — браузер **не** ходит на Backend (отвечает Service Worker).

---

## 2. Быстрый старт

### 2.1. Только Frontend (демо на моках, бэкенд не нужен)

```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

MSW-аккаунты (пароль `demo1234`):


| Email               | Роль      |
| ------------------- | --------- |
| `candidate@demo.ru` | candidate |
| `employer@demo.ru`  | employer  |
| `admin@demo.ru`     | admin     |


Подробности UI/маршрутов: `[frontend/README.md](./frontend/README.md)`.

### 2.2. Backend + Postgres (локально)

Нужны: Python 3.12+, `[uv](https://docs.astral.sh/uv/)`, Postgres с БД/`user` из вашего локального `backend/.env` (файл не коммитится; образец — `.env.example` если есть, иначе см. `backend/TASKS.md`).

```bash
cd backend
# создайте/поправьте .env под ваш Postgres (user/password/db)
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
```

- Swagger / OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- Live: `GET http://localhost:8000/health/live`  
- Ready: `GET http://localhost:8000/health/ready`  
- API prefix: `**/api/v1**`

Seed-аккаунты (пароли demo-only, паттерн `*Pass123!`):


| Роль        | Email                         | Пароль              |
| ----------- | ----------------------------- | ------------------- |
| admin       | `admin@example.invalid`       | `AdminPass123!`     |
| employer    | `employer1@example.invalid`   | `EmployerPass123!`  |
| candidate A | `candidate.a@example.invalid` | `CandidatePass123!` |
| candidate B | `candidate.b@example.invalid` | `CandidatePass123!` |


### 2.3. Docker (Postgres + Backend)

Из корня репо (нужен Docker/OrbStack). В окружении должен быть задан `POSTGRES_PASSWORD` (и при необходимости остальные переменные compose). Секреты — только в локальном env, не в git.

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Backend: [http://localhost:8000](http://localhost:8000) · Postgres: `localhost:5432`.

### 2.4. Frontend ↔ реальный Backend (целевой режим)

1. Backend поднят на `:8000`, seed выполнен.
2. На фронте **выключить MSW** и указать базу API на `/api/v1` (см. `frontend/src/shared/config/env.ts` / Vite).
3. Проксировать `/api` → `http://localhost:8000` в `frontend/vite.config.ts` **или** включить CORS на бэке (`CORS_ORIGINS` уже допускает `http://localhost:5173`).
4. Помнить: **пути и формы ответов FE-mocks и BE сейчас не 1:1** — см. §5. Без адаптера клиент «как есть» на MSW-контракте к BE не заведётся.

---

## 3. Структура репозитория

```
LCT_Resonance/
├── README.md                 ← вы здесь (FE + BE)
├── compose.yaml              ← postgres + backend
├── frontend/
│   ├── src/
│   │   ├── app/              # router, layouts, guards
│   │   ├── pages/            # экраны по ролям
│   │   ├── entities/         # типы + domain UI
│   │   ├── features/         # auth, notifications
│   │   ├── mocks/            # MSW handlers + fixtures
│   │   └── shared/api/       # apiClient, endpoints (сейчас под MSW-пути)
│   ├── TECH_SPEC.md
│   └── UI_KIT.md
└── backend/
    ├── app/
    │   ├── api/v1/           # HTTP-роуты
    │   ├── services/         # бизнес-логика
    │   ├── models/           # SQLAlchemy
    │   ├── schemas/          # Pydantic DTO
    │   ├── integrations/     # FSP, matcher
    │   ├── seed/             # демо-данные
    │   └── core/             # config, security, errors, deps
    ├── alembic/              # миграции
    ├── contracts/            # dto.json (черновик контракта)
    ├── TASKS.md              # бэклог задач BE
    └── tests/
```

---

## 4. Auth (как договорились на бэке)

### 4.1. Что отдаёт Backend


| Шаг         | Method / Path                    | Поведение                                                                         |
| ----------- | -------------------------------- | --------------------------------------------------------------------------------- |
| Регистрация | `POST /api/v1/auth/register`     | `candidate` | `employer`; в dev может вернуть `verification_token`                |
| Верификация | `POST /api/v1/auth/verify-email` | обязательна до полноценного login (по политике сервиса)                           |
| Логин       | `POST /api/v1/auth/login`        | `access_token` в JSON + **HttpOnly** cookie `refresh_token` (`path=/api/v1/auth`) |
| Refresh     | `POST /api/v1/auth/refresh`      | cookie → новый access + ротация refresh                                           |
| Me          | `GET /api/v1/auth/me`            | `{ id, email, role, email_verified }`                                             |
| Logout      | `POST /api/v1/auth/logout`       | revoke session + clear cookie                                                     |


Каждый защищённый запрос:

```http
Authorization: Bearer <access_token>
Accept: application/json
X-Request-Id: <optional uuid>   # бэкенд эхоит в X-Request-Id ответа
```

### 4.2. Что делает Frontend сейчас (MSW)

- Логин → `{ accessToken, user }`, токен в memory + `sessionStorage`.
- Нет refresh-cookie flow, нет verify-email.
- При `401` на авторизованном запросе — logout.

**Для интеграции:** фронту нужно выровнять имена полей (`access_token` vs `accessToken`), добавить refresh/verify, базу `/api/v1`.

### 4.3. Роли


| Роль        | Кабинет UI     | Типичный доступ API                         |
| ----------- | -------------- | ------------------------------------------- |
| `candidate` | `/candidate/*` | профиль, FSP, тесты, свои офферы            |
| `employer`  | `/employer/*`  | компании, вакансии, matching search, офферы |
| `admin`     | `/admin/*`     | расширенный доступ (часть эндпоинтов)       |


---

## 5. Контракт API: Backend (истина) vs Frontend MSW

Источник правды для продакшена: **Backend OpenAPI** → [http://localhost:8000/docs](http://localhost:8000/docs)  
Клиентский список вызовов сейчас: `frontend/src/shared/api/endpoints.ts` (заточен под MSW).  
Референс моков: `frontend/src/mocks/handlers.ts`.

### 5.1. Ошибки Backend

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "human readable",
    "details": {},
    "request_id": "req_…"
  }
}
```

Frontend MSW часто отдаёт просто `{ "message": "…" }`. При подключении к BE — парсить `error.message` / `error.code`.

### 5.2. Карта эндпоинтов Backend (`/api/v1`)

#### Auth — `/auth`


| Method | Path                   | Кто    |
| ------ | ---------------------- | ------ |
| POST   | `/register`            | public |
| POST   | `/verify-email`        | public |
| POST   | `/resend-verification` | public |
| POST   | `/login`               | public |
| POST   | `/refresh`             | cookie |
| POST   | `/logout`              | auth   |
| GET    | `/me`                  | auth   |


#### Taxonomy — публичные справочники


| Method | Path               |
| ------ | ------------------ |
| GET    | `/specializations` |
| GET    | `/grades`          |
| GET    | `/skills`          |


#### Candidates — `/candidates`


| Method           | Path                   | Назначение         |
| ---------------- | ---------------------- | ------------------ |
| GET/PATCH/DELETE | `/me`                  | свой профиль       |
| PUT              | `/me/skills`           | навыки             |
| PUT/DELETE       | `/me/fsp-link`         | привязка ФСП       |
| POST             | `/me/fsp-sync`         | sync               |
| GET              | `/me/fsp-achievements` | свои достижения    |
| GET              | ``                     | список (пагинация) |
| GET              | `/{id}`                | публичная карточка |
| GET              | `/{id}/achievements`   | чужие FSP          |


#### Tests — `/tests`


| Method | Path                    | Назначение             |
| ------ | ----------------------- | ---------------------- |
| POST   | `/attempts`             | старт попытки          |
| GET    | `/attempts/me`          | история                |
| GET    | `/attempts/{id}`        | состояние              |
| POST   | `/attempts/{id}/submit` | сдать / получить score |


> FE MSW использует другой стиль: `/tests/sessions/:id/question|answer|finish`.

#### Companies — `/companies`

CRUD компаний работодателя: `POST ""`, `GET /me`, `GET|PATCH|DELETE /{id}`.

#### Vacancies


| Method           | Path                      |
| ---------------- | ------------------------- |
| POST             | `/vacancies`              |
| GET              | `/vacancies`              |
| GET              | `/companies/me/vacancies` |
| GET/PATCH/DELETE | `/vacancies/{id}`         |
| POST             | `/vacancies/{id}/publish` |
| POST             | `/vacancies/{id}/close`   |


> FE MSW: `/employer/vacancies`, нет publish/close как отдельных действий.

#### Matching — `/matching`


| Method | Path      | Кто             |
| ------ | --------- | --------------- |
| POST   | `/search` | employer, admin |


Тело: `vacancy_id` и/или `need` (specialization/grade/skills/salary/format) + `limit`/`offset`.  
Ответ: `{ items: [{ candidate, match }], total, matcher }`.

> FE MSW: `GET /candidates?vacancyId=` с match в каждом item. Это **другой** контракт — при интеграции FE должен звать `POST /matching/search`.

#### Offers — `/offers`


| Method | Path                      | Назначение                   |
| ------ | ------------------------- | ---------------------------- |
| POST   | ``                        | создать (employer)           |
| GET    | ``                        | список по роли               |
| GET    | `/{id}`                   | детали                       |
| POST   | `/{id}/view`              | viewed                       |
| POST   | `/{id}/accept`            | принять                      |
| POST   | `/{id}/reject`            | отклонить (**не** `decline`) |
| POST   | `/{id}/withdraw`          | отозвать (employer)          |
| GET    | `/{id}/candidate-contact` | контакты после accept        |


> FE MSW: `decline` вместо `reject`; contacts через `GET /candidates/:id/contacts`.

### 5.3. Главные расхождения (чеклист интеграции)


| Тема                                                                           | Frontend (MSW)                  | Backend                                        |
| ------------------------------------------------------------------------------ | ------------------------------- | ---------------------------------------------- |
| Prefix                                                                         | `/api`                          | `/api/v1`                                      |
| Login body/out                                                                 | `accessToken`, `user`           | `access_token`, cookie refresh, отдельно `/me` |
| Talent Pool                                                                    | `GET /candidates?…`             | `POST /matching/search` + `GET /candidates`    |
| Decline offer                                                                  | `/decline`                      | `/reject`                                      |
| Contacts                                                                       | `/candidates/:id/contacts`      | `/offers/:id/candidate-contact`                |
| Testing                                                                        | sessions/question/answer/finish | attempts + submit                              |
| Companies                                                                      | часто захардкожены в оффере     | отдельный CRUD `/companies`                    |
| Errors                                                                         | `{ message }`                   | `{ error: { code, message, request_id } }`     |
| ID                                                                             | строковые `cand-1`, `vac-1`     | UUID                                           |
| Notifications / completeness / AI parse / compare / skill-radar / admin UI API | есть на FE                      | части нет или иначе — уточнять по TASKS / docs |


Пока живёте на MSW — разрабатывайте UI спокойно. Перед хакатонным E2E с BE — пройти таблицу выше и править `endpoints.ts` + типы.

---

## 6. Happy path (сквозной сценарий)

Ожидаемое поведение продукта (и DoD P0):

1. Employer регистрируется / логинится, создаёт **company**, публикует **vacancy**.
2. Candidate заполняет профиль, skills, (опционально) FSP sync, (опционально) тест.
3. Employer делает **matching search** по вакансии → видит score + reasons.
4. Employer шлёт **offer** с явной зарплатой.
5. Candidate **view → accept** (или reject).
6. Employer запрашивает **candidate-contact** — только после accept; иначе 403/ошибка приложения.
7. Match/test **не** считаются на фронте.

На MSW этот путь уже прогоняется тестами (`frontend` p0.dod). На BE — `tests/integration/test_golden_path.py` (нужен живой `DATABASE_URL`).

---

## 7. База данных

- СУБД: PostgreSQL 16 (compose) / локальный инстанс.  
- Миграции: Alembic (`uv run alembic upgrade head`).  
- Сиды: `uv run python -m app.seed` (идемпотентно: повтор → `SEED_SKIP`).  
- Основные таблицы: `users`, `candidate_profiles`, `companies`, `vacancies`, `offers`, `fsp_*`, `test_*`, taxonomy (`skills`, `grades`, `specializations`), …

Смотреть схему: DBeaver → `fsphack` → `public` → Tables (после migrate). Если пусто — миграции не гоняли.

---

## 8. Кто что правит


| Зона                                        | Owner            | Не ломать без синка                          |
| ------------------------------------------- | ---------------- | -------------------------------------------- |
| `backend/app/api`, `schemas`, OpenAPI       | Backend          | контракт для FE                              |
| `frontend/src/shared/api`, `entities/types` | Frontend         | после смены OpenAPI                          |
| `frontend/src/mocks/*`                      | Frontend         | только демо; не копировать формулы в prod UI |
| `frontend/UI_KIT.md`, `shared/ui`, tokens   | Frontend         | визуал                                       |
| `backend/integrations/fsp`, `matching`      | Backend          | адаптеры                                     |
| `compose.yaml`, миграции                    | Backend / DevOps |                                              |


Правило: **сначала контракт (OpenAPI / schemas), потом UI**. MSW подтягивать к BE, а не наоборот, когда начинается интеграция.

---

## 9. Скрипты (шпаргалка)

### Frontend

```bash
npm run dev        # :5173
npm run build
npm run test       # vitest + MSW
npm run lint
```

### Backend

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
uv run pytest tests/unit -q
```

### Compose

```bash
docker compose up -d --build
docker compose logs -f backend
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

