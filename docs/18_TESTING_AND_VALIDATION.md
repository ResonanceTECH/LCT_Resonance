# 18. Тестирование и валидация

---

## 1. Проверка matching

| Параметр | Факт |
| -------- | ---- |
| Датасет | синтетический demo batch в `ml/tests/fixtures_demo.py` + backend seed |
| Кандидаты ML batch | 15 |
| Вакансии ML batch | 4 |
| Экспертная разметка пар | отсутствует как отдельный gold-set от организаторов |
| Baseline | BaselineMatcher = та же формула 50/25/15/10 |
| Метрики Precision@K / NDCG@K | **не посчитаны** на размеченном наборе; не выдумываем числа |

Что реально проверяется автотестами:

```bash
cd ml && uv run pytest -q
cd backend && uv run pytest tests/unit/test_matching.py -q
```

Проверки: монотонность сортировки, anna > weak-stack, unverified FSP → fsp=0, skill_match 75% на эталонном кейсе, contract score ≈82.5.

**Предлагаемая методика** (если нет gold labels): экспертная разметка top-K глазами HR на seed-вакансиях; сравнение keyword-only vs full score; фиксация Kendall tau порядка. Фактических таблиц экспертизы в репо нет.

---

## 2. Проверка тестирования компетенций

Автотесты:

```bash
cd backend
uv run pytest tests/unit/test_testing_logic.py tests/unit/test_question_generators.py -q
```

Покрыто: plan_questions, blueprint, детерминизм generators, SQL/Python/JS ответы generators.  
Полной психометрики (IRT, различающая способность) **нет**.  
Сопоставимость вариантов — через общий blueprint и percent score / 10.

---

## 3. Backend-тесты

Фреймворк: pytest + pytest-asyncio.

```bash
cd backend
uv run pytest tests/unit -q
uv run pytest tests/integration -q   # нужен Postgres + seed
```

Ключевые integration: `test_golden_path.py`, `test_frontend_contract.py`, `test_seed_demo.py`, `test_passport.py`.

Интеграционные тесты Backend в среде подготовки документации: **не прогнаны** (нужен живой Postgres + seed). Unit — см. прогон ниже в §4/§3 итогах.

---

## 4. Frontend-тесты

```bash
cd frontend
npm run test
npm run lint
npm run build
```

Vitest + Testing Library + MSW. E2E браузерного раннера нет.  
DoD: `src/shared/api/p0.dod.test.ts` и связанные p2/p3.

**Проверено при подготовке docs:** `npm run test` → **23** файла, **60** тестов, все passed.

---

## 5. Проверка безопасности (ручные / частичные)

Фактически заложены в коде и частично в тестах:

| Сценарий | Ожидание |
| -------- | -------- |
| Без токена на protected | 401 |
| Чужая роль | 403 / редирект UI |
| Чужие офферы | недоступны |
| Contacts до Accept | CONTACTS_LOCKED |
| Admin API без admin | 403 |

Это **не** полноценный security audit.

---

## 6. Скриншоты

Каталог `docs/assets/screenshots/` подготовлен. Реальные скриншоты UI в среде документации **не сняты** (стенд мог быть не запущен). Не подставлять макеты как «скрины работающего интерфейса». При наличии стенда рекомендуется сохранить:

landing, login, candidate dashboard, testing, employer talent-pool, offer, contacts after accept, admin overview.
