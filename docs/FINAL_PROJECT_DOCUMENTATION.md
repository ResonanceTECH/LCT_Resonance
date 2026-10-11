# FSP Talent — итоговая техническая и пользовательская документация

**Продукт:** FSP Talent (репозиторий LCT Resonance)  
**Конкурс:** специальный трек ЛЦТ / Федерация спортивного программирования  
**Тип документа:** единый том для экспертизы и экспорта в PDF  
**Язык:** русский  
**Версия документации:** по состоянию исходного кода monorepo на момент подготовки  

Фирменные цвета (ориентир оформления): основной `#402FFF`, акцент `#EC1D35`, графит `#1B1C21`, светлый `#EDEDED`.

> Адреса стенда ниже указаны текстом (без гиперссылок) — удобно для PDF.  
> Официальный PDF ТЗ ФСП в репозитории не обнаружен; требования сверены с кодом и внутренними спецификациями команды.

---

## Содержание

1. Аннотация  
2. Контекст задачи и проблема  
3. Описание продукта и Reverse Recruitment  
4. Целевая аудитория  
5. Функциональность кандидата  
6. Функциональность работодателя  
7. Административная функциональность  
8. Архитектура  
9. Технологический стек  
10. Модель данных  
11. API  
12. Система тестирования и категоризация  
13. Matching и объяснимость  
14. Интеграция с ФСП  
15. Приватность и безопасность  
16. Валидация и тесты  
17. Инструкция развёртывания  
18. Руководство проверки (демо)  
19. Ограничения и развитие  
20. Заключение  
21. Приложения  

Детализация по темам также разнесена по файлам `docs/01_…` … `docs/23_…`.

---

## 1. Аннотация

FSP Talent — платформа обратного рекрутинга для ИТ: кандидат подтверждает профессиональную категорию тестированием, работодатель получает ранжированную подборку с объяснимым Match Score и отправляет персональное приглашение с зарплатой в рублях; контакты раскрываются только после принятия предложения (или отклика кандидата).

Решение сдаётся как monorepo: React-клиент, FastAPI Backend, PostgreSQL, опциональный explainable ML-сервис матчинга, Docker Compose стенд с Mailpit. Интеграция с реестром ФСП на хакатоне демонстрационная (mock-адаптер), отсутствие достижений ФСП корректно обрабатывается.

---

## 2. Контекст задачи и проблема

Поиск ИТ-специалистов часто сводится к ключевым словам в резюме. Работодателю сложно проверить квалификацию до интервью; кандидату — доказать уровень без длинного коммерческого трека; контакты утекают слишком рано.

Платформа отвечает тремя механиками: (1) подтверждённая категория через тест; (2) Talent Pool только по этой категории + explainable ranking; (3) gate на контакты на стороне Backend.

---

## 3. Описание продукта и Reverse Recruitment

Основной сценарий:

Кандидат регистрируется → заполняет профиль (специализация, заявленный грейд, навыки) → проходит тест → при балле ≥ 70 получает подтверждённую категорию → попадает в подборку → работодатель описывает потребность вакансией → видит ранжированный список с причинами → отправляет оффер с зарплатой → кандидат Accept/Decline → контакты открываются по правилам Backend.

Это не парсер вакансий и не классическая доска «откликнись первым». Работодатель сам выбирает специалиста. Опубликованная вакансия не является единственным способом существования потребности: поддерживаются статусы вроде draft; подбор привязан к `vacancyId` в Talent Pool.

---

## 4. Целевая аудитория

**Кандидаты:** Junior–Senior (также Intern/Lead в справочнике) в Frontend, Backend, Fullstack, Mobile, DevOps, Data Science, QA; с ФСП и без.

**Работодатели:** ИТ-компании, HR, техлиды.

**Админ:** операционный контроль (доп. модуль).

---

## 5. Функциональность кандидата

| Возможность | Маршрут UI | API / статус |
| ----------- | ---------- | ------------ |
| Регистрация / логин | `/register`, `/login` | auth OK |
| Подтверждение email | письмо / Mailpit | OK |
| Профиль | `/candidate/profile` | GET/PATCH me |
| Тест | `/candidate/testing` | tests sessions |
| ФСП | `/candidate/fsp` | mock sync |
| Офферы | `/candidate/offers` | accept/decline |
| Вакансии / отклики | `/candidate/vacancies` | доп. сценарий OK |
| Паспорт | `/p/:slug` | web, не server PDF |
| Импорт PDF резюме | — | нет |

Демо: `candidate@demo.ru` / `demo1234`.

---

## 6. Функциональность работодателя

| Возможность | Маршрут | Статус |
| ----------- | ------- | ------ |
| Вакансии (потребность) | `/employer/vacancies` | OK |
| Talent Pool | `/employer/talent-pool` | OK |
| Карточка + оффер | `/employer/candidates/:id` | OK |
| Shortlist / Compare | `/employer/shortlist`, `/compare` | OK |
| Контакты после Accept | contacts API | OK |
| Аналитика | dashboard | OK |

Демо: `employer@demo.ru` / `demo1234`.

---

## 7. Административная функциональность

Вход: `admin@demo.ru` / `demo1234` → `/admin/overview`.  
Users block/unblock; списки offers/vacancies/assessments/categories (в основном read). Не обязательный кабинет ТЗ.

---

## 8. Архитектура

```text
Browser → nginx :8080 (UI + /api proxy)
            → FastAPI :8000
                 → PostgreSQL 16
                 → Matcher (baseline in-process | HTTP ML :8001)
                 → FSPAdapter (mock | real stub)
                 → SMTP / Mailpit
```

Схема-изображение: файл `docs/assets/architecture/architecture.jpg`.

Модульный монолит Backend; микросервисов auth/assessment отдельных нет. Frontend по умолчанию в Docker ходит в реальный API (`VITE_USE_MOCKS=false`). MSW — opt-in для UI без Backend и для Vitest.

---

## 9. Технологический стек

- Frontend: React 19, TypeScript 5.8, Vite 6, React Router 7, TanStack Query 5, RHF, Zod, MSW, Vitest; nginx 1.27  
- Backend: Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, Argon2, PyJWT, asyncpg/psycopg, Uvicorn, uv  
- ML: FastAPI rule-based scoring (без torch/embeddings)  
- Data: PostgreSQL 16  
- Infra: Docker Compose, Mailpit; заготовки Render/Neon/Vercel  

Подробнее: `docs/21_TECH_STACK_AND_LICENSES.md`.

---

## 10. Модель данных

Ключевые таблицы: `users`, `auth_sessions`, `email_verification_tokens`, `candidate_profiles`, `candidate_skills`, `consents`, `companies`, `vacancies`, `vacancy_skills`, `offers`, `test_questions`, `test_attempts`, `test_attempt_items`, `fsp_links`, `fsp_achievements`, `shortlist_items`, `applications`, `saved_vacancies`, `notifications`, `profile_views`, `audit_events`, taxonomy (`specializations`, `grades`, `skills`).

Инварианты: declared ≠ verified grade; fail не даунгрейдит verified; контакты не в обычном profile DTO; Match Score не хранится как история ранжирования.

Миграции: `backend/alembic/versions/0001_initial_schema.py`, `0002_passport_token.py`.  
Seed: `uv run python -m app.seed`, пароль демо `demo1234`.

---

## 11. API

Префикс `/api`. Swagger: путь `/api/docs` на хосте Backend (порт 8000 или через nginx 8080). OpenAPI JSON: `/api/openapi.json`.

Группы: auth, taxonomy, candidates (me + Talent Pool + contacts), employer, vacancies, offers, tests, notifications, dashboards, admin, public passports.

Ошибка: `{ message, code, details, requestId }`.  
Пример блокировки контактов: код `CONTACTS_LOCKED`.

Полная таблица методов: `docs/07_API_REFERENCE.md`.

Пример:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"employer@demo.ru","password":"demo1234"}'
```

---

## 12. Система тестирования и категоризация

- 10 вопросов: static банк + generated по blueprint  
- Порог 70; пропуск = ошибка  
- Correct не отдаётся на Frontend  
- Retry cooldown 24ч (тот же/выше grade.rank)  
- Смена confirmed категории: cooldown 90 дней  
- Категория Talent Pool = verified specialization + verified grade  

Подтверждённая категория — единственный пропуск в пул вакансии этой пары.

---

## 13. Matching и объяснимость

```text
score = 0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions
```

Жёсткий фильтр категории → мягкий score.  
Навыки: required×2, nice×1; нормализация алиасов (React.js→React, TS→TypeScript, Postgres→PostgreSQL).  
FSP: только verified; пустой ФСП = 0 без исключения из пула.  
Reasons: SKILLS_REQUIRED, TEST_SCORE, FSP_VERIFIED, SALARY_MISMATCH, …  

`MATCHER_PROVIDER=baseline` (default) или `ml` с fallback. Обученных нейросетей нет.

Демо-порядок на Frontend Middle (ML batch): anna выше weak-stack; см. `docs/08_ML_MATCHING.md`.

---

## 14. Интеграция с ФСП

Официального API нет. Реализован `MockFSPAdapter` (JSON fixtures) и контрактный `RealFSPAdapter`. Sync после согласия `fsp_sync`. Формулировки «официально подтверждено ФСП» для mock недопустимы. Keycloak не внедрён.

---

## 15. Приватность и безопасность

Argon2 пароли; JWT access 8ч; refresh HttpOnly; RBAC; rate limits; email verify; contacts только после Accept/Apply; consents с версией.  
152-ФЗ как юридический аудит не заявляется. Секреты `.env` не публикуются.

Матрица видимости — `docs/11_AUTH_AND_SECURITY.md`.

---

## 16. Валидация и тесты

```bash
cd frontend && npm run test
cd backend && uv run pytest tests/unit -q
cd backend && uv run pytest tests/integration -q
cd ml && uv run pytest -q
```

Golden path: `test_golden_path.py`, `p0.dod.test.ts`.  
Frontend при подготовке docs: `npm run test` → 23 файла / 60 тестов passed.  
Backend unit / ML pytest: зависят от `uv` в PATH; integration — нужен Postgres.  
Precision@K / NDCG@K на экспертной разметке **не публиковались** — не выдуманы.  
Полноценный security audit не проводился.

---

## 17. Инструкция развёртывания (кратко)

Требования: Docker Compose; для локальной разработки — Python 3.12+, Node 20+, uv, Postgres 16.

```bash
# корень репозитория
# файл .env: POSTGRES_PASSWORD=DemoPass123
# backend/.env из example с JWT_SECRET
docker compose up -d --build
```

Открыть: http://localhost:8080 — UI; http://localhost:8080/api/docs — Swagger; http://localhost:8025 — почта.

Локально: Postgres/Mailpit из compose → `uv run uvicorn` на 8000 → `npm run dev` на 5173.

Подробно: `docs/12_INSTALLATION.md`, `SETUP.md`.

---

## 18. Руководство проверки за 5–10 минут

1. `docker compose up -d --build`  
2. Браузер → http://localhost:8080  
3. Войти `employer@demo.ru` / `demo1234` → Talent Pool по вакансии → увидеть score и причины  
4. Войти `candidate@demo.ru` / `demo1234` → офферы → Accept  
5. Снова employer → контакты доступны  
6. Проверить сценарий «до Accept контакты закрыты»  
7. Кандидат без ФСП остаётся в пуле  

Полные сценарии A–H: `docs/17_DEMO_SCENARIOS.md`.  
Пошаговые клики: `docs/14_USER_GUIDE_CANDIDATE.md`, `docs/15_USER_GUIDE_EMPLOYER.md`.

---

## 19. Ограничения и развитие

Ограничения: mock ФСП; ограниченный банк тестов; синтетика matching без gold NDCG; нет server PDF; нет Keycloak; нет embeddings; публичный URL стенда не зафиксирован в репо.

Развитие: реальный реестр ФСП, OIDC, ATS, расширение taxonomy/тестов, semantic rerank при сохранении explainability, PDF passport.

---

## 20. Заключение

FSP Talent реализует проверяемый MVP обратного рекрутинга с подтверждением грейда, explainable matching и контролем контактов. Стенд воспроизводится через Docker Compose; контракт API задокументирован OpenAPI; ключевой happy path покрыт автотестами. Документация описывает **фактический** код и честно отделяет mock/частичные и отсутствующие элементы.

---

## 21. Приложения

### A. Карта документов `docs/`

| Файл | Тема |
| ---- | ---- |
| 01_PROJECT_OVERVIEW.md | обзор |
| 02_FUNCTIONAL_REQUIREMENTS.md | матрица функций |
| 03_ARCHITECTURE.md | архитектура |
| 04_DATABASE.md | БД |
| 05_FRONTEND.md | клиент |
| 06_BACKEND.md | сервер |
| 07_API_REFERENCE.md | API |
| 08_ML_MATCHING.md | matching |
| 09_ASSESSMENT_SYSTEM.md | тесты компетенций |
| 10_FSP_INTEGRATION.md | ФСП |
| 11_AUTH_AND_SECURITY.md | безопасность |
| 12_INSTALLATION.md | установка |
| 13_CONFIGURATION.md | env |
| 14_USER_GUIDE_CANDIDATE.md | гид кандидата |
| 15_USER_GUIDE_EMPLOYER.md | гид работодателя |
| 16_ADMIN_GUIDE.md | админ |
| 17_DEMO_SCENARIOS.md | демо жюри |
| 18_TESTING_AND_VALIDATION.md | валидация |
| 19_TROUBLESHOOTING.md | проблемы |
| 20_LIMITATIONS_AND_ROADMAP.md | ограничения |
| 21_TECH_STACK_AND_LICENSES.md | стек |
| 22_REQUIREMENTS_TRACEABILITY.md | трассировка ТЗ |
| 23_SUBMISSION_GUIDE.md | сдача |

Корневые материалы: `README.md`, `SETUP.md`, `APPROACH.md`, `CJM.md`, `Backend.md`, `Frontend.md`, `ML.md`.

### B. Демо-аккаунты

Пароль: `demo1234`  
`admin@demo.ru`, `employer@demo.ru`, `employer2@demo.ru`, `candidate@demo.ru`, `elena@demo.ru`, `maxim@demo.ru`, …

### C. Неизвестное / не проверено при подготовке docs

- Текст официального PDF ТЗ (файл отсутствует)  
- Стабильный публичный URL стенда  
- Прогон полного pytest/npm test в среде агента на момент генерации  
- Реальные скриншоты UI (каталог `docs/assets/screenshots` пуст)  
- Экспорт PDF/DOCX (нет pandoc/weasyprint в среде) — выполнить локально из этого MD  

### D. Чек-лист готовности стенда

- [ ] compose up успешен  
- [ ] health/ready ok  
- [ ] логин employer и candidate  
- [ ] Talent Pool со score  
- [ ] Accept → contacts  
- [ ] Swagger открывается  
