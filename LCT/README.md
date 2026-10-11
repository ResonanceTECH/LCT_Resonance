# Resonance ML

Сервис матчинга вакансии и резюме. Backend — единственный клиент выдачи: он уже фильтрует Talent Pool и вызывает `POST /rank`. Frontend в ML не ходит.

Формула основного score не меняется (её ждут контракт и baseline):

```text
score = 0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions
```

Контентная близость — отдельный сигнал отбора, в `score` она не прибавляется.

## Как устроено ранжирование

1. **Офлайн** (`python -m app.offline.build` или `POST /offline/rebuild`). По резюме и вакансиям из мини-БД заново считаются контентные векторы и инвертированный индекс `content_postings`.
2. **Онлайн-отбор.** Запрос (вакансия или резюме пользователя) ищется по общим токенам: специализация, грейд, нормализованные навыки, формат работы, дисциплина ФСП. Required-навыки вакансии весят ×2. Похожесть — косинус.
3. **Мэтчер** (`app/matcher.py`). Для пары вакансия ↔ резюме считает explainable score, пересечение навыков, флаги зарплаты и формата, коды причин.
4. **Реранкер** (`app/reranker.py`). Порядок: score → вклад теста → category score → контентная близость → `candidateId`.

`POST /rank` считает только тех кандидатов, которых прислал Backend. Каталог для этого пути не нужен. `POST /online/rank-resumes` и `POST /online/rank-vacancies` сначала читают мини-БД.

## Мини-БД

SQLite-файл из `DATABASE_PATH` (по умолчанию `data/resonance.db`, в Docker — `/data/resonance.db` на volume `ml-data`). Схема создаётся при старте.

| Таблица | Откуда в Backend | Что хранит |
|---|---|---|
| `resumes` | `candidate_profiles`, `candidate_skills`, `fsp_achievements` | JSON резюме в контракте матчера и контентный вектор |
| `vacancies` | `vacancies`, `vacancy_skills` | JSON вакансии и контентный вектор |
| `content_postings` | — | токен → документ, строится офлайн и при каждой записи |

DDL лежит в `app/db/schema.sql`. При старте его читает `app/db/store.py` (в пакете файл кладётся в wheel; если файла нет, используется запасная копия в коде).

## Контракт, который вызывает Backend

`HttpMatcher` бьёт в `POST {ML_MATCHER_URL}/rank`. Тело и ответ — camelCase, `modelVersion = ml-v1`. Коды причин те же, что в `REASON_LABELS` на Backend; подписи рисует Backend.

Эти ручки Backend собирают пакет и отдают его в `/rank`:

| Backend | Зачем ML |
|---|---|
| `GET /api/candidates` | Talent Pool работодателя |
| `GET /api/vacancies/{id}/matches` | кандидаты под вакансию |
| `GET /api/vacancies/{id}/match-to-me` | одно резюме пользователя против вакансии |
| `GET /api/vacancies` | лента вакансий с match для кандидата |

Авторизация, офферы, тесты и ФСП API остаются на Backend. Сюда приходит уже готовый `testScore` и `verified`.

## Эндпоинты ML

| Метод | Назначение |
|---|---|
| `GET /health` | сервис жив |
| `POST /rank` | пакетный score для Backend |
| `POST /match` | одна пара вакансия + резюме |
| `POST /normalize-skills` | `React.js` → `React` |
| `POST /categorize` | мягкая категория, не замена теста |
| `POST /grade-status` | заявленный грейд не переписывается |
| `POST /category-rank` | порядок внутри «специализация / грейд» |
| `PUT /catalog/resumes` | положить резюме в мини-БД и проиндексировать |
| `GET /catalog/resumes` | список резюме |
| `PUT /catalog/vacancies` | положить вакансию |
| `GET /catalog/vacancies` | список вакансий |
| `POST /offline/rebuild` | пересобрать индекс |
| `POST /online/rank-resumes` | вакансия → резюме из БД |
| `POST /online/rank-vacancies` | резюме пользователя → вакансии из БД |
| `POST /online/similar-resumes` | резюме пользователя → похожие резюме |

## Локально

```bash
uv sync --group dev
uv run uvicorn app.main:app --reload --port 8001
uv run pytest
```

Офлайн-пересчёт индекса:

```bash
uv run python -m app.offline.build
```

## Docker

Образ — `Dockerfile`: Python 3.12, зависимости из `pyproject.toml`, uvicorn на порту 8001, база в `/data/resonance.db`.

Compose поднимает один сервис `ml` и volume `ml-data` (это и есть мини-БД):

```bash
docker compose up -d --build
curl -s localhost:8001/health
```

Пересобрать индекс в уже запущенном контейнере:

```bash
docker compose exec ml python -m app.offline.build
```

Чтобы Backend ходил в этот сервис, в его окружении:

```bash
MATCHER_PROVIDER=ml
ML_MATCHER_URL=http://ml:8001
```

Если ML недоступен, Backend остаётся на `BaselineMatcher` с той же формулой.
