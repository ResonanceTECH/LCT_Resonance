# 08. ML Matching и подбор кандидатов

Код: `ml/app/` и `backend/app/integrations/matching/`. Продуктовая логика: `APPROACH.md`, спецификация: `ML.md`.

**Важно:** в репозитории нет обученных нейросетей и embeddings. «ML-сервис» — explainable rule-based scoring на FastAPI с расширенными эндпоинтами. Основной score Talent Pool совпадает с BaselineMatcher.

---

## 1. Постановка задачи

**Вход (вакансия / потребность):** специализация, грейд, required/nice skills, work_format, salary_to, опционально текст.

**Вход (кандидат):** confirmed specialization+grade, test_score, skills, salary_from, work_format, verified FSP achievements, readiness.

**Выход:** упорядоченный список matches: score 0–100, components, reasons (коды + labels на Backend), matched/missing skills.

---

## 2. Две ступени

1. **Жёсткий фильтр (Backend):** в пул по `vacancyId` только кандидаты с той же confirmed парой spec+grade, readiness ≠ not_looking, видимые работодателям (email verified и т.д.).
2. **Мягкий score:** сортировка внутри пула.

Специализацию в формуле повторно не начисляют — она уже в фильтре.

---

## 3. Нормализация навыков

ML: `ml/app/skills/dictionary.py` (~120 алиасов). Ключ = lowercase alphanumeric.  
Примеры: React.js/ReactJS → React; TS → TypeScript; Postgres/PostgreSQL → PostgreSQL.

Backend: урезанный словарь в `backend/app/services/skills.py` (subset OK).

Неизвестный навык остаётся как есть. Missing skill в ответе = «не указан в профиле», не «не умеет».

---

## 4. Формула Match Score (Talent Pool)

```text
score = 0.50·test_raw + 0.25·skills_raw + 0.15·fsp_raw + 0.10·conditions_raw
```

| Компонент | Вес | Расчёт |
| --------- | --- | ------ |
| test | 50% | test_score если in_category, иначе 0 |
| skills | 25% | weighted: required×2, nice×1 |
| fsp | 15% | только verified; participation/finalist/prize; bonus sport_rank; в ML ещё +relevance |
| conditions | 10% | 50% формат + 50% зарплата; неизвестность = NEUTRAL 50 |

`modelVersion`: `baseline-v1` или `ml-v1`.

Диагностическая формула 40/25/15/10/10 со specialization из ML.md — **не** primary score API.

---

## 5. Explainability

Коды причин (примеры): `SKILLS_REQUIRED`, `SKILLS_OPTIONAL`, `TEST_SCORE`, `GRADE_CONFIRMED`, `FSP_VERIFIED`, `FSP_RELEVANT`, `WORK_FORMAT_MATCH|MISMATCH`, `SALARY_MATCH|MISMATCH`, …

`positive: false` показывается как минус в UI.

---

## 6. Пример на seed-данных (ML demo batch)

Вакансия Frontend Middle (`vac-fe-middle`), прогон тестов ML:

| candidateId | score (окр.) | Комментарий |
| ----------- | ------------ | ----------- |
| anna | ~85.2 | сильный стек + FSP + conditions |
| salary-high | ~81.2 | выше тест, но salary mismatch режет conditions |
| no-fsp-fe | ~65.9 | без FSP, fsp=0 |
| elena | ~57.6 | слабее skills/conditions |
| weak-stack | ~44.0 | нет пересечения навыков |

Воспроизведение:

```bash
cd ml
uv sync --group dev
uv run pytest tests/test_demo_batch.py tests/test_ranking.py -q
```

---

## 7. Как Backend вызывает matcher

```text
MATCHER_PROVIDER=baseline (default) → in-process
MATCHER_PROVIDER=ml → POST http://ml:8001/rank (compose) или localhost:8001
ошибка/таймаут → BaselineMatcher
```

Frontend **никогда** не вызывает ML напрямую.

---

## 8. Что не реализовано

Embeddings, обученные модели, LLM-разбор вакансий в ML, вызов `/categorize` из Backend в прод-пути. Парсер вакансий Backend — эвристики по словарю БД (`POST /vacancies/parse`).
