# LCT Resonance

Веб-сервис **обратного рекрутинга**: работодатель ищет кандидатов (Talent Pool + Match Score + ФСП), кандидат получает офферы и принимает/отклоняет. Контакты кандидата открываются **только после Accept** (или собственного отклика кандидата), на стороне Backend.

Спец.трек хакатона. Репозиторий — monorepo:


| Папка                            | Стек                                         | Порт (dev) | Документация                                                                       |
| -------------------------------- | -------------------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| [`frontend/`](./frontend/)       | React 19, Vite, TanStack Query, MSW          | `:5173`    | [`frontend/README.md`](./frontend/README.md), [`UI_KIT.md`](./frontend/UI_KIT.md) |
| [`backend/`](./backend/)         | FastAPI, SQLAlchemy, Alembic, PostgreSQL     | `:8000`    | [`backend/README.md`](./backend/README.md)                                         |
| [`compose.yaml`](./compose.yaml) | Postgres, backend, frontend (nginx), Mailpit | `:8080`    | ниже                                                                               |

Требования: [`Backend.md`](./Backend.md), [`Frontend.md`](./Frontend.md), [`ML.md`](./ML.md), [`CJM.md`](./CJM.md).

**Контракт API один:** Backend реализует то, что вызывает фронтенд — пути из `frontend/src/shared/api/endpoints.ts`, типы из `frontend/src/entities/types.ts`, поведение из `frontend/src/mocks/handlers.ts` (как требует `Backend.md`). Это проверяет тест `backend/tests/integration/test_frontend_contract.py`.

---

## 1. Продуктовые границы (обязательно читать обеим ролям)


| Делает Backend                                  | Делает Frontend                                      |
| ----------------------------------------------- | ---------------------------------------------------- |
| Auth (JWT), RBAC, подтверждение email           | UI логина/регистрации, хранение access token, guards |
| Match Score / ranking / Skill Radar / аналитика | Только отображение DTO                               |
| Генерация вопросов, правильные ответы, оценка   | Вопросы без `correct`, прогресс, UI результата       |
| FSP sync через адаптер, согласия                | Кнопка sync, согласие, список достижений             |
| Раскрытие контактов после Accept                | Показ контактов **только** из успешного API          |
| Аудит, уведомления, валидация бизнес-правил     | Валидация форм (Zod), empty/loading/error            |


Анти-цели фронта: не считать match/test на клиенте; не ходить в ФСП напрямую; не «раскрывать» контакты по статусу оффера в обход API.

```
Browser (React)  →  /api (Vite proxy или nginx)  →  Backend  →  Postgres
                                                       ↓
                                       FSP adapter / Matcher (baseline | ML)
```

---

## 2. Быстрый старт

Пошаговая инструкция для новых участников команды, настройка почты и частые проблемы —
в [`SETUP.md`](./SETUP.md).

### 2.1. Весь стенд в Docker (рекомендуется для демо)

Нужны Docker/OrbStack, `POSTGRES_PASSWORD` в окружении или корневом `.env`, `backend/.env` из `backend/.env.example` (минимум `JWT_SECRET`).

```bash
docker compose up -d --build
```

UI + API: [http://localhost:8080](http://localhost:8080) · Swagger: [http://localhost:8080/api/docs](http://localhost:8080/api/docs) · письма подтверждения: [http://localhost:8025](http://localhost:8025) (Mailpit).
Миграции и демо-сиды применяются при старте backend. Подробности (prod-режим, SMTP, лимиты) — в [`backend/README.md`](./backend/README.md).

### 2.2. Локально: Backend + Frontend

```bash
# backend (Python 3.12+, uv, Postgres из backend/.env)
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000

# frontend (в другом терминале): Vite проксирует /api на :8000
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Swagger: [http://localhost:8000/api/docs](http://localhost:8000/api/docs) · Health: `GET /api/health/live`, `GET /api/health/ready`.

### 2.3. Только Frontend на моках (бэкенд не нужен)

```bash
cd frontend
VITE_USE_MOCKS=true npm run dev
```

### 2.4. Демо-аккаунты

Одинаковые для моков и для реального Backend, пароль `demo1234` (только для демо-стенда):


| Роль      | Email               | Профиль                                      |
| --------- | ------------------- | -------------------------------------------- |
| admin     | `admin@demo.ru`     | Админ Resonance                              |
| employer  | `employer@demo.ru`  | Игорь Смирнов, Resonance Labs                |
| employer  | `employer2@demo.ru` | Ольга Петрова, ТехноСфера                    |
| candidate | `candidate@demo.ru` | Анна Ковалёва, Frontend middle, тест 82, ФСП |
| candidate | `maxim@demo.ru` …   | ещё 4 именованных + 8 фоновых кандидатов     |

Демо-пара для ранжирования и mock-ID ФСП — в [`backend/README.md`](./backend/README.md).

---

## 3. Структура репозитория

```
LCT_Resonance/
├── README.md                 ← вы здесь (FE + BE)
├── compose.yaml              ← postgres + backend + frontend (nginx) + mailpit
├── frontend/
│   ├── src/
│   │   ├── app/              # router, layouts, guards
│   │   ├── pages/            # экраны по ролям
│   │   ├── entities/         # типы (контракт) + domain UI
│   │   ├── features/         # auth, notifications
│   │   ├── mocks/            # MSW handlers + fixtures (демо без backend)
│   │   └── shared/api/       # apiClient, endpoints
│   ├── Dockerfile, nginx.conf
│   └── UI_KIT.md
└── backend/
    ├── app/
    │   ├── api/routes/       # HTTP-роуты под /api
    │   ├── services/         # бизнес-логика
    │   ├── models/           # SQLAlchemy
    │   ├── schemas/          # Pydantic DTO (camelCase)
    │   ├── integrations/     # FSP, matcher, email
    │   ├── seed/             # демо-данные
    │   └── core/             # config, security, errors, deps, rate limit
    ├── alembic/              # миграции
    └── tests/                # unit + integration (golden path, контракт с фронтом)
```

---

## 4. Auth

| Шаг              | Method / Path                         | Поведение                                                                                          |
| ---------------- | ------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Регистрация      | `POST /api/auth/register`             | `{ email, password, role, displayName }` → `{ accessToken, user }`, письмо со ссылкой подтверждения |
| Логин            | `POST /api/auth/login`                | `{ accessToken, user }`; неподтверждённый email вход не блокирует                                   |
| Me               | `GET /api/auth/me`                    | `AuthUser` + `emailVerified`                                                                        |
| Logout           | `POST /api/auth/logout`               | отзыв сессии                                                                                        |
| Подтверждение    | ссылка из письма / `POST /api/auth/verify-email` | `{ ok: true }`                                                                           |
| Повторное письмо | `POST /api/auth/resend-verification`  | `{ ok: true }`                                                                                      |

Access token живёт 8 часов (у фронта нет refresh), передаётся в `Authorization: Bearer …`. Пока email не подтверждён: работодатель не может отправлять офферы (`403 EMAIL_NOT_VERIFIED`), кандидат не виден в Talent Pool. Фронт показывает баннер с кнопкой «Отправить ещё раз».

---

## 5. Контракт API (`/api`)

Ошибки — плоский объект, фронт показывает `message`:

```json
{ "message": "Контакты доступны после принятия предложения", "code": "CONTACTS_LOCKED", "details": {}, "requestId": "req_…" }
```

| Группа              | Пути                                                                                                                                                |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Справочники         | `GET /specializations`, `/grades`, `/skills?q=`                                                                                                     |
| Кандидат: профиль   | `GET/PATCH/DELETE /candidates/me`, `GET /candidates/me/completeness`, `GET/PUT /candidates/me/consents`                                             |
| Кандидат: ФСП       | `GET /candidates/me/fsp/achievements`, `POST /candidates/me/fsp/sync`, `PUT/DELETE /candidates/me/fsp/link`                                         |
| Talent Pool         | `GET /candidates?specialization&grade&skills&workFormat&salaryFrom&salaryTo&fspDiscipline&hasFspAchievements&readiness&vacancyId&q&sort&page&limit` |
| Карточка кандидата  | `GET /candidates/{id}`, `/{id}/contacts`, `/{id}/fsp/achievements`, `/{id}/skill-radar`                                                             |
| Работодатель        | `GET/POST /employer/vacancies`, `GET /employer/offers`, `GET/POST /employer/shortlist`, `DELETE /employer/shortlist/{id}`, `GET /employer/candidates/compare?ids=`, `GET/PUT /employer/company` |
| Вакансии            | `GET /vacancies?specialization&matchToMe&savedOnly`, `GET/PATCH /vacancies/{id}`, `GET /vacancies/{id}/match-to-me`, `POST /vacancies/{id}/apply`, `POST /vacancies/parse` |
| Кандидат: коллекции | `GET /candidate/offers`, `GET /candidate/saved-vacancies`, `POST/DELETE /candidate/saved-vacancies/{id}`                                            |
| Офферы              | `POST /offers`, `GET /offers/{id}` (первое открытие кандидатом → `viewed`), `POST /offers/{id}/accept`, `/decline`                                  |
| Тесты               | `POST /tests/sessions`, `GET …/{id}/question`, `POST …/{id}/answer`, `POST …/{id}/finish`, `GET …/{id}/result`, `GET /tests/history`               |
| Уведомления         | `GET /notifications`, `POST /notifications/{id}/read`, `POST /notifications/read-all`                                                               |
| Дашборды            | `GET /dashboard/candidate`, `/dashboard/employer`, `/dashboard/employer/analytics`                                                                  |
| Admin               | `GET /admin/overview`, `/admin/users`, `POST /admin/users/{id}/status`, `GET /admin/offers`, `/admin/vacancies`                                     |
| Career Passport     | `GET /candidates/me/passport` (своя ссылка `/p/<имя>-<токен>` и почему она скрыта), `GET /public/passports/{slug}` без auth, только с согласием на публикацию; ищется по токену, внутренний id в ссылке не участвует |

Полные схемы — Swagger. Изменение контракта: менять `frontend/src/entities/types.ts` и backend schemas вместе — контрактный тест ловит рассинхрон.

---

## 6. Happy path (сквозной сценарий)

1. Employer регистрируется, подтверждает email, создаёт **вакансию** (компания создаётся из `companyName`).
2. Candidate заполняет профиль и навыки, синхронизирует ФСП (с согласием), проходит **тест** → подтверждённая категория.
3. Employer открывает Talent Pool по вакансии → **score + причины** (плюсы и минусы).
4. Employer отправляет **оффер** с зарплатой в рублях.
5. Candidate открывает оффер (`viewed`) → **accept** (или decline).
6. Employer видит **контакты** — только после accept; до этого `403 CONTACTS_LOCKED`.
7. Match/test **не** считаются на фронте.

Автотесты: фронт — `frontend/src/shared/api/p0.dod.test.ts` (на MSW); бэкенд — `backend/tests/integration/test_golden_path.py` (на Postgres).

---

## 7. База данных

- PostgreSQL 16 (compose) или локальный инстанс; миграции Alembic (`uv run alembic upgrade head`, проверка рассинхрона моделей — `uv run alembic check`).
- Сиды: `uv run python -m app.seed` (идемпотентно: повтор → `SEED_SKIP`).
- Основные таблицы: `users`, `candidate_profiles`, `companies`, `vacancies`, `offers`, `fsp_*`, `test_*`, `notifications`, `shortlist_items`, `applications`, `saved_vacancies`, `consents`, taxonomy.

---

## 8. Кто что правит


| Зона                                           | Owner              | Не ломать без синка                          |
| ---------------------------------------------- | ------------------ | -------------------------------------------- |
| `frontend/src/entities/types.ts`, `shared/api` | Frontend + Backend | контракт: менять вместе, контрактный тест    |
| `backend/app/api`, `schemas`, OpenAPI          | Backend            | контракт для FE                              |
| `frontend/src/mocks/*`                         | Frontend           | только демо; не копировать формулы в prod UI |
| `frontend/UI_KIT.md`, `shared/ui`, tokens      | Frontend           | визуал                                       |
| `backend/integrations/fsp`, `matching`         | Backend            | адаптеры                                     |
| `compose.yaml`, миграции                       | Backend / DevOps   |                                              |

---

## 9. Скрипты (шпаргалка)

### Frontend

```bash
npm run dev                       # :5173, /api → :8000
VITE_USE_MOCKS=true npm run dev   # демо на MSW
npm run build
npm run test                      # vitest + MSW
npm run lint
```

### Backend

```bash
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
uv run pytest tests/unit -q          # без БД
uv run pytest tests/integration -q   # нужен мигрированный и засиженный Postgres
```

### Compose

```bash
docker compose up -d --build      # миграции и сиды — при старте backend
docker compose logs -f backend
```
