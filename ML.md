# ТЗ для ML-разработчика

## 1. Задача ML-модуля

ML-модуль обрабатывает профили кандидатов и требования работодателей: нормализует навыки, подсказывает категорию, считает соответствие вакансии, ранжирует выдачу и объясняет, почему кандидат оказался выше.

В MVP три основные задачи:

1. Категоризация по профессиональному направлению.
2. Расчёт соответствия кандидата вакансии (Match Score).
3. Ранжирование кандидатов с понятными причинами результата.

На вход могут идти:

- данные профиля;
- заявленные навыки;
- заявленный грейд;
- результат теста;
- подтверждённые достижения ФСП;
- требования вакансии;
- карьерные предпочтения (формат работы, ожидания по зарплате).

ФСП - дополнительный подтверждённый сигнал, а не доказательство стека. Участие в соревновании само по себе не значит, что кандидат знает React или Python.

Реализация: сервис `ml/` (FastAPI). Frontend в ML не ходит. Клиент для матчера - только Backend (`MATCHER_PROVIDER=ml`, `ML_MATCHER_URL`). При недоступности ML Backend падает на локальный `BaselineMatcher` с той же формулой Talent Pool.

Связанные документы: `APPROACH.md` (продуктовая логика), `Backend.md` (контракт и жёсткий фильтр Talent Pool), `ml/README.md` (как поднять сервис).

## 2. Функциональные требования

### ML-01. Нормализация навыков

Разные написания одного навыка нужно сводить к одному ключу, иначе matching считает `React.js` и `React` разными вещами.

Примеры:

```text
React.js  → React
ReactJS   → React
JS        → JavaScript
TS        → TypeScript
Postgres  → PostgreSQL
Py        → Python
```

Вход:

```json
["React.js", "TS", "Postgres"]
```

Выход:

```json
["React", "TypeScript", "PostgreSQL"]
```

Эндпоинт: `POST /normalize-skills`. Словарь синонимов живёт в `ml/app/skills/dictionary.py`; в Backend для хранения профиля используется совместимый нормализатор.

### ML-02. Категоризация кандидата

ML определяет профессиональное направление. Минимальный набор для MVP:

```text
Frontend
Backend
Mobile
ML / Data Science
Data Engineering
DevOps
QA
Cybersecurity
Algorithms
Other
```

Учитываем специализацию, которую выбрал кандидат, навыки, опыт, данные ФСП, дисциплины и роли в соревнованиях. Выбранная кандидатом специализация весит больше косвенных признаков.

Пример ответа `POST /categorize`:

```json
{
  "candidateId": 15,
  "category": "Frontend",
  "confidence": 0.91,
  "reasons": [
    "Кандидат указал специализацию Frontend",
    "В профиле указаны React и TypeScript"
  ]
}
```

Важно: в Talent Pool по вакансии категория для допуска - это подтверждённая тестом пара «специализация + грейд» на Backend. ML-категоризация - мягкая подсказка и сигнал для внутренних сценариев, а не замена теста.

### ML-03. Работа с грейдом

Кандидат сам указывает предполагаемый уровень: Intern, Junior, Middle, Senior.

Результат теста - дополнительный сигнал. Система не должна автоматически понижать заявленный грейд, если тест слабее ожидания.

Пример `POST /grade-status`:

```json
{
  "declaredGrade": "Middle",
  "testScore": 62,
  "gradeStatus": "not_confirmed"
}
```

Запрещённый сценарий: тихая замена `Middle → Junior`. Балл теста может влиять на положение внутри категории и на Match Score, но не на переписывание заявленного грейда.

### ML-04. Обработка данных ФСП

Структурированные достижения ФСП идут в ranking как признаки. Типичный вход (после подготовки на Backend):

```json
{
  "discipline": "Программирование продуктовое",
  "title": "Название соревнования",
  "placeOrResult": "2 место",
  "sportRank": "1 разряд",
  "verified": true,
  "achievementType": "prize"
}
```

ML не меняет флаг `verified`. Данные приходят уже подготовленными через FSP Adapter / Mock API.

Из достижений можно собрать, например:

- есть ли подтверждённые записи;
- сколько их;
- релевантна ли дисциплина вакансии / стеку;
- есть ли разряд;
- тип результата (участие, финал, приз).

Пустой список достижений - нормальный случай (см. ML-10).

## 3. Matching кандидата и вакансии

### ML-05. Расчёт Match Score

Для пары кандидат + вакансия модуль возвращает соответствие в диапазоне 0-100.

Полноценную обученную модель на хакатоне не требуем и не предпочитаем. Нужен объяснимый scoring.

Черновик весов из ранней версии ТЗ:

| Критерий | Вес |
|----------|-----|
| Совпадение навыков | 40% |
| Специализация | 25% |
| Тест / подтверждение уровня | 15% |
| Релевантные достижения ФСП | 10% |
| Формат и предпочтения | 10% |

В продукте Talent Pool Backend уже жёстко фильтрует по специализации и подтверждённому грейду. Поэтому для основного `/rank` принята формула без повторного начисления специализации:

```text
score = 0.50·test + 0.25·skills + 0.15·fsp + 0.10·conditions
```

Вариант 40/25/15/10/10 остаётся диагностическим (мягкий / межкатегорийный анализ), не основным score выдачи. Подробнее - в `APPROACH.md`.

Зарплату не предсказываем. Это отдельное условие совместимости: ожидание кандидата от 200 000 ₽ при потолке вакансии 120 000 ₽ должно явно помечаться как несовпадение.

### ML-06. Matching навыков

Вакансия:

```json
{
  "requiredSkills": ["React", "TypeScript", "Redux", "Git"]
}
```

Кандидат:

```json
{
  "skills": ["React", "TypeScript", "Git", "Python"]
}
```

Результат:

```json
{
  "matchedSkills": ["React", "TypeScript", "Git"],
  "missingInProfileSkills": ["Redux"]
}
```

Формулировка: «не указан в профиле», а не «кандидат не знает Redux». Отсутствие строки в анкете не доказывает отсутствие навыка.

В формуле обязательные навыки весят сильнее желательных (required ×2, nice-to-have ×1). В ответе сохраняем написание из вакансии, сравнение идёт по нормализованному ключу.

## 4. Объяснимость результата

### ML-07. Match Explanation

К каждому Match Score нужны причины. Без этого работодателю бесполезен голый процент.

Пример смысла (тексты подписей собирает Backend по кодам):

```json
{
  "candidateId": "15",
  "vacancyId": "7",
  "score": 87,
  "matchedSkills": ["React", "TypeScript", "Git"],
  "missingInProfileSkills": ["Redux"],
  "reasons": [
    { "code": "SPECIALIZATION_MATCH", "params": { "specialization": "Frontend" }, "positive": true },
    { "code": "SKILLS_REQUIRED", "params": { "matched": 3, "total": 4 }, "positive": false },
    { "code": "WORK_FORMAT_MATCH", "params": { "workFormat": "remote" }, "positive": true },
    { "code": "FSP_VERIFIED", "params": { "count": 1 }, "positive": true }
  ]
}
```

Нужно не «87% Match», а «87%, потому что совпали специализация, 3 из 4 навыков, формат работы и есть подтверждённые достижения ФСП».

Словарь кодов и шаблонов label держит Backend (`Backend.md`), чтобы baseline и внешний ML говорили одинаково.

## 5. Ранжирование кандидатов

### ML-08. Ranking

После расчёта score кандидатов по вакансии нужно отсортировать. Эндпоинт: пакетный `POST /rank` (вакансия + список кандидатов).

```json
[
  { "candidateId": "12", "score": 92 },
  { "candidateId": "17", "score": 86 },
  { "candidateId": "31", "score": 79 }
]
```

При равенстве score порядок стабилизируем вкладом теста, затем внутренним category score, затем `candidateId`.

### ML-09. Ранжирование внутри категории

Категория здесь: специализация + грейд, например `Frontend / Junior`, `Backend / Middle`.

Внутри категории можно упорядочивать по тесту, заполненности релевантной части профиля, подтверждённым достижениям ФСП и широте / релевантности навыков. Эндпоинт: `POST /category-rank`.

```json
{
  "category": "Frontend / Junior",
  "candidateId": "15",
  "categoryScore": 84
}
```

В MVP не обязательно показывать «место №17 среди Junior Frontend». Достаточно использовать score для сортировки.

## 6. Кандидаты без данных ФСП

### ML-10. Пустой ФСП

```json
{ "fspAchievements": [] }
```

это не ошибка. Score считается по остальным доступным данным: специализация, навыки, опыт, грейд, тест, предпочтения. Отсутствие истории ФСП само по себе не выкидывает кандидата из выдачи; вклад компонента `fsp` просто равен нулю.

## 7. Контракт Backend ↔ ML

Frontend → Backend → ML → Backend → Frontend. Единая точка API для клиента - Backend.

Пакетный вызов на одну выдачу. JSON в camelCase (как остальной API).

### Вход `POST /rank`

```json
{
  "vacancy": {
    "id": "vac-1",
    "specialization": "Frontend",
    "requiredGrade": "middle",
    "requiredSkills": ["React", "TypeScript"],
    "niceToHaveSkills": ["Jest", "Vite"],
    "salaryFrom": 260000,
    "salaryTo": 340000,
    "workFormat": "remote"
  },
  "candidates": [
    {
      "id": "6f0c2c1e-...",
      "specialization": "Frontend",
      "confirmedGrade": "middle",
      "declaredGrade": "middle",
      "testScore": 82,
      "skills": ["React", "TypeScript", "CSS", "Vite", "Redux"],
      "experienceYears": 4,
      "salaryFrom": 250000,
      "salaryTo": 320000,
      "workFormat": "remote",
      "fspAchievements": [
        {
          "id": "fsp-1",
          "title": "Кубок ФСП по веб-разработке",
          "discipline": "Продуктовое программирование",
          "placeOrResult": "2 место",
          "sportRank": "1 разряд",
          "verified": true,
          "achievementType": "prize"
        }
      ]
    }
  ]
}
```

Схемы: `backend/app/schemas/matcher_contract.py` и `ml/app/schemas.py`.

### Ответ

```json
{
  "matches": [
    {
      "candidateId": "6f0c2c1e-...",
      "score": 85,
      "matchedSkills": ["React", "TypeScript", "Vite"],
      "missingInProfileSkills": ["Jest"],
      "reasons": [
        { "code": "SPECIALIZATION_MATCH", "params": { "specialization": "Frontend" }, "positive": true },
        { "code": "SKILLS_REQUIRED", "params": { "matched": 2, "total": 2 }, "positive": true },
        { "code": "FSP_VERIFIED", "params": { "count": 1 }, "positive": true }
      ],
      "components": { "test": 41, "skills": 20.8, "fsp": 13.5, "conditions": 10 },
      "category": "Frontend / Middle",
      "categoryScore": 84,
      "gradeStatus": "confirmed",
      "salaryCompatible": true,
      "workFormatCompatible": true
    }
  ],
  "modelVersion": "ml-v1"
}
```

`components` и диагностические поля нужны для отладки и защиты; во Frontend DTO они не обязаны уходить. Подписи причин рендерит Backend.

Дополнительно у ML-сервиса:

| Метод | Назначение |
|-------|------------|
| `GET /health` | Жив ли сервис |
| `POST /normalize-skills` | ML-01 |
| `POST /categorize` | ML-02 |
| `POST /grade-status` | ML-03 |
| `POST /category-rank` | ML-09 |
| `POST /rank` | ML-05…08, ML-10 |

## 8. Что относится к ML, а что нет

Границы лучше зафиксировать сразу, иначе команда начнёт дублировать работу.

| Задача | Ответственный |
|--------|---------------|
| Хранение профиля и вакансии | Backend |
| Получение данных ФСП, проверка `verified` | Backend / FSP Adapter |
| Хранение и проведение тестов | Backend + Frontend |
| Нормализация навыков | ML (+ совместимый слой в Backend при записи профиля) |
| Категоризация (мягкая) | ML |
| Match Score, ranking, причины | ML (или baseline-fallback на Backend) |
| Приглашения, контакты, CRUD, авторизация | Backend |
| Отображение Match Score | Frontend |
| Фильтры интерфейса | Frontend + Backend |

ML не занимается пользователями, авторизацией, офферами, контактами, CRUD вакансий и прямым ФСП API.

## 9. Тестирование и ML

Генерацию вопросов через LLM на ML не вешаем.

Тест нужен, чтобы подтвердить заявленный грейд, но это не значит, что ML должен собирать и проверять сессии.

```text
Кандидат выбирает грейд (например Junior)
        ↓
Проходит тест специализации / грейда
        ↓
Backend считает и хранит результат
        ↓
ML получает testScore
        ↓
Балл учитывается в ranking
```

Пример: Junior Frontend, test score 82/100. Для ML это один из признаков.

Автогенерация заданий через LLM может быть продуктовой гипотезой, но не P0. Сборка теста (шаблоны / static) описана в `APPROACH.md` и `Backend.md`.

## 10. Приоритеты на хакатон

### P0 - обязательно

1. Зафиксировать вход и выход с Backend (camelCase, пакетный `/rank`).
2. Нормализовать навыки.
3. Категоризировать кандидатов (мягкая модель).
4. Реализовать explainable Match Score.
5. Учитывать результат теста.
6. Учитывать подтверждённые достижения ФСП.
7. Ранжировать кандидатов под вакансию.
8. Возвращать причины matching.
9. Корректно работать без FSP achievements.
10. Отдать Backend стабильный контракт; при падении ML демо живёт на baseline.

### P1 - если P0 готов

- расширенный словарь синонимов;
- более точная релевантность дисциплин ФСП;
- раздельный учёт must-have / nice-to-have в объяснениях;
- калибровка весов на демо-выборке;
- семантическое сравнение текста вакансии и профиля.

### P2 - только если останется время

Это скорее продуктовые гипотезы, чем обязательные требования исходного ТЗ:

- embeddings;
- LLM-разбор текста вакансии;
- автоизвлечение стека из description;
- AI-рекомендации кандидату;
- сложная персонализация ranking.

На 4-дневном хакатоне отдельную модель «ради галочки ML» не обучаем. Без нормального датасета объяснимый scoring надёжнее и проще защищается перед жюри.

## 11. Definition of Done

ML-часть MVP готова, если Backend передаёт кандидата (или пакет) и вакансию, а в ответ получает score, пересечение навыков, флаги совместимости и причины. Пример смысла ответа:

```json
{
  "score": 91,
  "category": "Frontend / Junior",
  "matchedSkills": ["React", "TypeScript", "Git"],
  "missingInProfileSkills": ["Redux"],
  "salaryCompatible": true,
  "reasons": [
    { "code": "SPECIALIZATION_MATCH", "params": { "specialization": "Frontend" }, "positive": true },
    { "code": "SKILLS_REQUIRED", "params": { "matched": 3, "total": 4 }, "positive": false },
    { "code": "WORK_FORMAT_MATCH", "params": { "workFormat": "remote" }, "positive": true },
    { "code": "TEST_SCORE", "params": { "score": 82 }, "positive": true },
    { "code": "FSP_VERIFIED", "params": { "count": 1 }, "positive": true }
  ]
}
```

На этой основе Backend отдаёт работодателю отсортированный список кандидатов с Match Score и причинами.

### План на первые дни (ориентир)

**День 1.** Согласовать с Backend JSON-контракт, категории, признаки, словарь навыков, формулу Talent Pool.

**День 2.** Нормализация навыков, категоризация, baseline matching.

**День 3.** ФСП, тест, ranking, explainability. Прогон на 10-20 кандидатах и 3-5 вакансиях.

**День 4.** Интеграция, крайние случаи, фиксация весов, стабильные demo results.

Главный риск интеграции: разойтись по формату данных. Контракт нужно зафиксировать до параллельной работы, иначе на третий день придётся переписывать стык.
