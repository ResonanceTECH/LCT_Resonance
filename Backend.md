# Функциональные требования к Backend 

Backend должен обеспечить один главный сквозной сценарий: **кандидат регистрируется, проходит профилирование и тестирование, связывает профиль с ФСП, получает категорию, после чего работодатель описывает потребность, получает ранжированную подборку кандидатов и отправляет конкретному человеку приглашение с обязательной зарплатой. Кандидат принимает или отклоняет приглашение, а его контакты раскрываются работодателю только после принятия.** Именно обратная механика подбора является смысловым центром текущего ТЗ и получает самый большой вес при оценке, 35%.

Важное уточнение по актуальному PDF ТЗ: **на хакатоне реального API ФСП и описания структуры данных не предоставляют**. Команда сама проектирует предполагаемую интеграцию и работает на синтетических данных. Поэтому для MVP нужен `FSPAdapter` с двумя реализациями: рабочий `MockFSPAdapter` для демо и контрактный `RealFSPAdapter`, который можно подключить после появления реального API. ТЗ также прямо требует корректно обрабатывать кандидата без истории ФСП. 

Рекомендуемый стек: **Python + FastAPI + PostgreSQL + SQLAlchemy + Alembic**. Для 4-дневного хакатона это должен быть модульный монолит, а не набор микросервисов. FastAPI автоматически формирует OpenAPI-схему и Swagger UI, что напрямую помогает выполнить требование ТЗ о документированном API. SQLAlchemy закрывает ORM-слой, а Alembic предназначен для версионируемых миграций реляционной БД. 

**P0-функции Backend:**

- регистрация и подтверждение email;
- JWT-аутентификация и RBAC;
- профиль кандидата;
- специализации, грейды и навыки;
- тестирование и присвоение категории;
- FSP Mock Integration;
- компания работодателя;
- описание потребности / вакансия;
- поиск и фильтрация кандидатов;
- matching и explainable ranking;
- приглашения работодателя;
- принятие / отклонение;
- безопасное раскрытие контактов;
- seed-данные;
- OpenAPI;
- Docker deployment.

Допущение: все методы доступны под префиксом `/api` — это `apiBaseUrl` фронтенда по умолчанию. Источник истины для контракта — уже написанный фронтенд (ветка `frontend-dev`): `src/entities/types.ts`, `src/shared/api/endpoints.ts` и `src/mocks/handlers.ts`. Backend подстраивается под него, а требования ТЗ, которых во фронтенде пока нет, перечислены в разделе «Чего не хватает во фронтенде».

---

## Модель данных и права доступа

**Главный принцип модели данных:** не складывать всё про кандидата в одну таблицу `users`. Разделяем authentication, профессиональный профиль, результаты тестирования, навыки и подтверждённые данные ФСП. Тогда позже интеграцию с Keycloak или реестром ФСП можно заменить без переделки всей модели.

### ER-модель

| Сущность | Ключевые поля | Связи | Зачем нужна |
|----|----|----|----|
| `users` | id UUID, email, password_hash, role (candidate / employer / admin), display_name, email_verified_at, status (active / blocked), timestamps | 1:1 CandidateProfile или 1:1 Company | аккаунт и роль |
| `auth_sessions` | id (= `sid` в JWT), user_id, expires_at, revoked_at, user_agent | N:1 User | logout и отзыв токенов |
| `email_verification_tokens` | user_id, token_hash, expires_at, used_at | N:1 User | подтверждение email |
| `candidate_profiles` | id UUID (= `candidateId` в API), user_id, full_name, specialization, claimed_grade, confirmed_grade, readiness, work_format, salary_from, salary_to, … | 1:1 User | профессиональный профиль |
| `specializations` | name (PK), sort_order | 1:N Candidate / Vacancy / Template | Frontend, Backend, … |
| `grades` | code (PK), rank | 1:N Candidate / Vacancy / Template | intern … lead |
| `skills` | id, name (каноническое), synonyms | M:N Candidates / Vacancies | справочник навыков и синонимов |
| `candidate_skills` | candidate_id, skill_id | bridge | стек кандидата |
| `companies` | id, owner_user_id, name, description, industry, contact_email, website | 1:1 Employer | профиль компании |
| `vacancies` | id, employer_id, company_name, title, description, specialization, required_grade, salary_from, salary_to, currency, city, work_format, extra_info, status | N:1 Employer | потребность работодателя |
| `vacancy_skills` | vacancy_id, skill_id, required | bridge | обязательные и дополнительные навыки |
| `question_templates` | specialization, grade, topic, tags, difficulty, kind (generated / static), generator_key, static_payload, exposure_count, status | N:1 taxonomy | банк шаблонов и static-вопросов |
| `test_sessions` | id, candidate_id, specialization, stack, claimed_grade, status, current_index, total_questions, score, grade_confirmed, is_retest, timestamps | N:1 Candidate | сессия тестирования |
| `test_session_items` | session_id, position, template_id, seed, text, code, options, correct_option_id, selected_option_id, is_correct | N:1 Session | выданные экземпляры и ответы |
| `fsp_links` | candidate_id, fsp_member_id, sync_status, last_synced_at, raw_snapshot | 1:1 Candidate | связь с ФСП |
| `fsp_achievements` | id, candidate_id, source, external_id, title, discipline, achieved_at, place_or_result, participant_role, sport_rank, achievement_type, place | N:1 Candidate | подтверждённые достижения |
| `offers` | id, employer_id, candidate_id, vacancy_id nullable, company_name, position_title, message, salary_from, salary_to, currency, work_format, employer_contact, status | N:1 Candidate / Employer | обратный рекрутинг |
| `applications` | id, candidate_id, vacancy_id, created_at | N:1 Candidate / Vacancy | классический отклик, P1 |
| `shortlist_items` | employer_id, candidate_id, created_at | bridge | shortlist работодателя, P1 |
| `saved_vacancies` | candidate_id, vacancy_id, created_at | bridge | избранные вакансии, P1 |
| `notifications` | id, user_id, type, title, body, href, read_at, created_at | N:1 User | уведомления |
| `profile_views` | candidate_id, employer_id, viewed_at | N:1 Candidate | счётчик для дашборда кандидата |
| `consents` | user_id, type, version, accepted_at, withdrawn_at | N:1 User | согласия на обработку и публикацию |
| `audit_events` | actor, action, entity_type, entity_id, metadata, created_at | N:1 User | аудит критичных действий |

`candidateId` во всех DTO — это `candidate_profiles.id`, а не `users.id`. `employerId` — это `users.id` работодателя. Так устроены типы фронтенда.

### Почему vacancy_id у приглашения nullable

Это прямое следствие ТЗ: работодатель должен иметь возможность выйти на человека без обязательной привязки приглашения к опубликованной вакансии.

То есть допустимы оба варианта:

```text
Employer → Vacancy → Candidate → Offer
```

и

```text
Employer → Candidate → Offer
```

Во втором случае само приглашение содержит позицию, описание работы и зарплатную вилку. Форма фронтенда сейчас всегда передаёт `vacancyId`, но API принимает и `null`.

### Профиль кандидата

Поля `candidate_profiles` повторяют `CandidateProfile` фронтенда (в БД snake_case, в API camelCase):

```text
id                      -- candidateId в API
user_id
full_name
about
specialization
claimed_grade           -- заявленный кандидатом
confirmed_grade         -- подтверждённый тестом, nullable
experience_years
experience_description
desired_position
salary_from
salary_to
currency                -- только RUB
city
work_format             -- remote | hybrid | office
readiness               -- actively_looking | open_to_offers | not_looking
phone                   -- контакт, раскрывается только после accept
telegram                -- контакт, раскрывается только после accept
last_grade_change_at
created_at
updated_at
```

Вычисляемые поля DTO: `skills` (из `candidate_skills`), `testResult` (последняя завершённая сессия), `fspSyncedAt` и `hasFspAchievements` (из `fsp_links` и `fsp_achievements`), `profileCompleteness`.

Здесь специально разделены:

```text
claimed_grade
confirmed_grade
```

Потому что кандидат сначала сам выбирает предполагаемый уровень, а дальше проходит тестирование. ТЗ отдельно говорит, что неуспешный тест не должен автоматически понижать кандидата.

Допущение: при провале теста `claimed_grade` остаётся прежним, а `confirmed_grade` не меняется. Такой кандидат не получает подтверждённую категорию, пока не пройдёт соответствующий тест.

### Навыки

API передаёт навыки строками с каноническими названиями, как во фронтенде: `skills`, `requiredSkills`, `niceToHaveSkills`. При записи Backend нормализует ввод через словарь синонимов (ML-01: `React.js` → `React`, `Postgres` → `PostgreSQL`) и хранит ссылки на справочник:

```text
skills
candidate_skills
vacancy_skills
```

Это сильно упрощает фильтрацию:

```sql
WHERE skill_id IN (...)
```

и не заставляет делать NLP там, где хватает обычного SQL. Неизвестный навык добавляется в справочник как новый, без синонимов.

### Ключевые индексы

Для поиска кандидатов и бизнес-правил нужны как минимум:

```sql
CREATE UNIQUE INDEX ux_users_email
ON users (lower(email));

CREATE UNIQUE INDEX ux_candidate_profiles_user
ON candidate_profiles (user_id);

CREATE INDEX ix_candidate_category
ON candidate_profiles (specialization, confirmed_grade, readiness);

CREATE INDEX ix_candidate_skills_skill
ON candidate_skills (skill_id, candidate_id);

CREATE INDEX ix_vacancies_search
ON vacancies (specialization, required_grade, status);

CREATE INDEX ix_offers_candidate_status
ON offers (candidate_id, status);

CREATE INDEX ix_offers_employer_status
ON offers (employer_id, status);

-- один активный оффер работодателя кандидату по вакансии
CREATE UNIQUE INDEX ux_offers_active_vacancy
ON offers (employer_id, candidate_id, vacancy_id)
WHERE status IN ('new', 'viewed') AND vacancy_id IS NOT NULL;

-- и один активный оффер без вакансии: NULL не участвует в обычном UNIQUE
CREATE UNIQUE INDEX ux_offers_active_no_vacancy
ON offers (employer_id, candidate_id)
WHERE status IN ('new', 'viewed') AND vacancy_id IS NULL;

CREATE UNIQUE INDEX ux_fsp_member
ON fsp_links (fsp_member_id);

CREATE UNIQUE INDEX ux_fsp_achievement
ON fsp_achievements (candidate_id, source, external_id);
```

B-tree в PostgreSQL подходит для типовых equality/range запросов, а индексы нужно добавлять осмысленно: они ускоряют чтение ценой дополнительной стоимости записи.

### Роли и права

| Операция | Candidate | Employer | Admin |
|----|---:|---:|---:|
| Редактировать свой профиль | ✅ | ❌ | ✅ |
| Смотреть свои FSP-данные | ✅ | ❌ | ✅ |
| Изменять FSP Verified данные вручную | ❌ | ❌ | P1 |
| Проходить тест | ✅ | ❌ | ❌ |
| Смотреть каталог кандидатов | ❌ | ✅ | ✅ |
| Смотреть контакты кандидата до Accept | ❌ | ❌ | только служебно |
| Создавать компанию | ❌ | ✅ | ✅ |
| Создавать вакансию | ❌ | ✅ | ✅ |
| Делать matching | ❌ | ✅ | ✅ |
| Отправлять приглашение | ❌ | ✅ | ✅ |
| Принимать приглашение | ✅, своё | ❌ | ❌ |
| Отклонять приглашение | ✅, своё | ❌ | ❌ |
| Смотреть других кандидатов | ❌ | ✅, без PII | ✅ |

ТЗ прямо запрещает кандидату доступ к другим кандидатам и запрещает работодателю видеть контакты человека до принятия приглашения или самостоятельного отклика.

### Схема аутентификации

Под фронтенд:

```text
email + password + displayName + role
       ↓
POST /auth/register → { accessToken, user }
       ↓
Bearer access JWT
       ↓
RBAC на каждом endpoint
```

Фронтенд хранит `accessToken` в памяти и `sessionStorage` и не умеет обновлять токен: refresh-запросов в клиенте нет, а на `401` он разлогинивает пользователя. Поэтому для MVP:

- access JWT живёт 8 часов;
- в JWT есть `sid`, сессия хранится в `auth_sessions`, logout её отзывает;
- refresh-токен с ротацией — P1, когда фронтенд добавит `/auth/refresh`;
- пароли хешируются Argon2id;
- PII в токен не кладём: payload подписан, но не зашифрован.

Access token:

```json
{
  "sub": "user_uuid",
  "role": "employer",
  "sid": "session_uuid",
  "iat": 1791370000,
  "exp": 1791398800
}
```

Подтверждение email обязательно по ТЗ, но не блокирует вход: фронтенд логинит пользователя сразу после регистрации. Пока email не подтверждён, кандидат не показывается в Talent Pool, а работодатель не может отправлять офферы (`403 EMAIL_NOT_VERIFIED`). Письмо со ссылкой уходит при регистрации.

Для будущей интеграции с ФСП authentication layer стоит спрятать за интерфейс:

```python
class AuthProvider:
    def authenticate(...)
    def validate_access_token(...)
    def get_user(...)
```

Тогда локальный JWT позже заменяется `KeycloakAuthProvider`. Это соответствует направлению ТЗ: ФСП планирует использовать Keycloak, который предоставляет стандартные OIDC endpoints (discovery, token, userinfo, JWKS).

## REST API и контракты между компонентами

Все методы доступны под `/api`. Контракт повторяет то, что уже вызывает фронтенд (ветка `frontend-dev`): пути — из `src/shared/api/endpoints.ts`, типы — из `src/entities/types.ts`, поведение — из `src/mocks/handlers.ts`. Методы, которые фронтенд пока не вызывает, помечены «фронт: нет».

JSON в API — camelCase, в БД — snake_case. В FastAPI это одна базовая схема:

```python
class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

Справочные значения совпадают с `src/shared/lib/labels.ts`:

```text
grade           intern | junior | middle | senior | lead
specialization  Frontend | Backend | Fullstack | Mobile | DevOps | Data Science | QA
workFormat      remote | hybrid | office
readiness       actively_looking | open_to_offers | not_looking
currency        RUB
```

Фронтовый тип допускает `USD`, но ТЗ требует вилку в рублях, поэтому на любую другую валюту Backend отвечает `422 CURRENCY_NOT_SUPPORTED`.

Списки: Talent Pool возвращает `{ "items": [], "total": 0 }` и принимает `page` и `limit` (не больше 50, по умолчанию 20). Остальные списки фронтенд ждёт массивом.

Ошибки — плоский объект, фронтенд показывает `message`:

```json
{
  "message": "Кандидат сейчас не рассматривает предложения",
  "code": "CANDIDATE_NOT_AVAILABLE",
  "details": {},
  "requestId": "req_a01f..."
}
```

Ошибки валидации Pydantic заворачиваются в тот же формат через обработчик `RequestValidationError`: `422`, `code = VALIDATION_ERROR`, список полей в `details.fields`. Статусы, на которые завязаны сценарии фронтенда: `400`, `401`, `403`, `404`.

### Auth API

| Метод | Endpoint | Вход | Выход |
|----|----|----|----|
| POST | `/auth/register` | email, password, role (candidate / employer), displayName | `{ accessToken, user }` |
| POST | `/auth/login` | email, password | `{ accessToken, user }` |
| POST | `/auth/logout` | Bearer | 204 |
| GET | `/auth/me` | Bearer | AuthUser |
| POST | `/auth/verify-email` | token из письма | `{ ok: true }`, фронт: нет |
| POST | `/auth/resend-verification` | Bearer | `{ ok: true }`, фронт: нет |

Регистрация:

```json
POST /api/auth/register
{
  "email": "anna@example.ru",
  "password": "StrongPassword123!",
  "role": "candidate",
  "displayName": "Анна Ковалёва"
}
```

Ответ:

```json
{
  "accessToken": "eyJhbGciOi...",
  "user": {
    "id": "9633c815-21c2-43ef-9818-b7428d60fbef",
    "email": "anna@example.ru",
    "role": "candidate",
    "displayName": "Анна Ковалёва",
    "emailVerified": false
  }
}
```

Для кандидата профиль создаётся сразу, как в моках: `fullName = displayName`, `readiness = open_to_offers`, `specialization = Frontend`, `claimedGrade = junior` до заполнения анкеты. В выдачу под вакансию такой кандидат не попадает, пока не подтвердит грейд тестом. Поле `emailVerified` фронтенд пока не читает. Ошибки: `409` «Email уже зарегистрирован», `401` «Неверный email или пароль», `403` «Аккаунт заблокирован».

### Candidate API

| Метод | Endpoint | Доступ | Назначение |
|----|----|----|----|
| GET | `/candidates/me` | Candidate | свой профиль, включая `phone` и `telegram` |
| PATCH | `/candidates/me` | Candidate | частичное обновление |
| GET | `/candidates/me/completeness` | Candidate | чек-лист заполненности |
| GET | `/candidates/{id}` | Employer, Admin | профиль без контактов |
| GET | `/candidates` | Employer, Admin | Talent Pool с фильтрами |
| GET | `/candidates/{id}/contacts` | Employer | контакты после accept или отклика |
| GET/PUT | `/candidates/me/consents` | Candidate | согласия, фронт: нет |
| GET | `/candidates/{id}/skill-radar` | Employer | Skill Radar, P2 |
| GET | `/employer/candidates/compare?ids=` | Employer | сравнение двух и более кандидатов, P2 |
| GET | `/public/passports/{slug}` | без auth | Career Passport, P2, только с согласием на публикацию |

Маршруты `/candidates/me/...` объявляются раньше `/candidates/{id}/...`, иначе FastAPI примет `me` за id.

CandidateProfile:

```json
{
  "id": "6f0c2c1e-...",
  "userId": "9633c815-...",
  "fullName": "Анна Ковалёва",
  "about": "Frontend-разработчик с фокусом на React",
  "specialization": "Frontend",
  "claimedGrade": "middle",
  "confirmedGrade": "middle",
  "experienceYears": 4,
  "experienceDescription": "SPA, дизайн-системы, code review",
  "skills": ["React", "TypeScript", "CSS", "Vite", "Redux"],
  "desiredPosition": "Frontend Engineer",
  "salaryFrom": 250000,
  "salaryTo": 320000,
  "currency": "RUB",
  "city": "Москва",
  "workFormat": "remote",
  "readiness": "open_to_offers",
  "testResult": {
    "score": 82,
    "maxScore": 100,
    "gradeConfirmed": true,
    "completedAt": "2026-09-12T10:00:00Z"
  },
  "fspSyncedAt": "2026-10-01T12:00:00Z",
  "hasFspAchievements": true,
  "profileCompleteness": 90
}
```

`PATCH /candidates/me` принимает любое подмножество редактируемых полей. `confirmedGrade`, `testResult`, `fspSyncedAt`, `hasFspAchievements` и `profileCompleteness` вычисляет Backend и при записи игнорирует. `phone` и `telegram` принимаются в PATCH и возвращаются только владельцу.

Query Talent Pool (`GET /candidates`):

| Параметр | Как работает |
|----|----|
| `specialization`, `workFormat`, `readiness` | точное совпадение |
| `grade` | по `confirmedGrade`: выдача строится на подтверждённой категории, а не на заявленной |
| `skills` | через запятую, должны быть все |
| `salaryFrom`, `salaryTo` | пересечение с вилкой ожиданий кандидата |
| `fspDiscipline`, `hasFspAchievements` | по подтверждённым достижениям ФСП |
| `q` | поиск по имени, специализации и навыкам |
| `vacancyId` | подбор под вакансию: hard filters, `match` в каждом item, сортировка по score |
| `sort` | `match`, `grade`, `salary`, `name` |
| `page`, `limit` | пагинация |

Ответ: `{ "items": TalentPoolItem[], "total": 8 }`, где `TalentPoolItem` = CandidateProfile без контактов + `match?`. Кандидаты с неподтверждённым email в выдачу не попадают.

### Taxonomy API

| Метод | Endpoint | Назначение |
|----|----|----|
| GET | `/specializations` | список специализаций |
| GET | `/grades` | список грейдов |
| GET | `/skills?q=react` | поиск навыков с учётом синонимов |

Фронтенд пока держит справочники в `labels.ts`, поэтому эти методы нужны для подсказок навыков и будущей замены хардкода. CRUD навыков для admin — P1.

### Testing API

Фронтенд проходит тест сессией, по одному вопросу:

| Метод | Endpoint | Вход | Выход |
|----|----|----|----|
| POST | `/tests/sessions` | specialization, stack[], claimedGrade, retest? | TestSession |
| GET | `/tests/sessions/{id}/question` | — | TestQuestion |
| POST | `/tests/sessions/{id}/answer` | questionId, optionId | TestSession |
| POST | `/tests/sessions/{id}/finish` | — | TestResult |
| GET | `/tests/sessions/{id}/result` | — | TestResult |
| GET | `/tests/history` | — | TestHistoryItem[] |

При старте Backend собирает тест по blueprint и сразу генерирует все экземпляры вопросов в `test_session_items` (см. «Механика тестирования»):

```json
{
  "id": "session-3f1a...",
  "specialization": "Frontend",
  "stack": ["React", "TypeScript"],
  "claimedGrade": "middle",
  "currentIndex": 0,
  "totalQuestions": 10,
  "status": "in_progress"
}
```

Вопрос:

```json
{
  "id": "item-901",
  "text": "Сколько строк вернёт запрос?",
  "code": "SELECT * FROM users u LEFT JOIN orders o ON o.user_id = u.id",
  "options": [
    { "id": "a", "text": "5" },
    { "id": "b", "text": "7" },
    { "id": "c", "text": "8" }
  ]
}
```

`id` вопроса — это id экземпляра в `test_session_items`, а не шаблона. Поле `code` необязательное, фронтенд его пока не показывает. Правильный ответ не уходит на фронтенд никогда, в том числе после `finish`.

Результат:

```json
{
  "sessionId": "session-3f1a...",
  "score": 82,
  "maxScore": 100,
  "gradeConfirmed": true,
  "completedAt": "2026-10-07T14:30:00Z",
  "claimedGrade": "middle",
  "isRetest": false
}
```

При `gradeConfirmed = true` Backend записывает `confirmedGrade = claimedGrade` сессии. `TestHistoryItem` = TestResult + `specialization`. Ограничение частоты смены грейда возвращает `409 GRADE_CHANGE_COOLDOWN` с `details.nextAvailableAt`.

### FSP API

| Метод | Endpoint | Доступ | Выход |
|----|----|----|----|
| GET | `/candidates/me/fsp/achievements` | Candidate | FspAchievementsResponse |
| POST | `/candidates/me/fsp/sync` | Candidate | FspAchievementsResponse |
| GET | `/candidates/{id}/fsp/achievements` | Employer | FspAchievementsResponse |
| PUT | `/candidates/me/fsp/link` | Candidate | `{ fspMemberId, linkedAt }`, фронт: нет |

```json
{
  "achievements": [
    {
      "id": "fsp-1",
      "title": "Кубок ФСП по веб-разработке",
      "discipline": "Продуктовое программирование",
      "date": "2025-11-10",
      "placeOrResult": "2 место",
      "participantRole": "Участник",
      "sportRank": "1 разряд",
      "verified": true
    }
  ],
  "syncedAt": "2026-10-07T14:00:00Z",
  "status": "synced"
}
```

`status` (`synced`, `no_history`, `stale`) — дополнительное поле: фронтенд пока различает «нет данных» по пустому массиву. Подробности — в «Контракт синхронизации».

### Vacancy API

| Метод | Endpoint | Доступ | Назначение |
|----|----|----|----|
| POST | `/employer/vacancies` | Employer | создать вакансию, status приходит из формы |
| GET | `/employer/vacancies` | Employer | свои вакансии |
| GET | `/vacancies/{id}` | авторизованные | просмотр |
| PATCH | `/vacancies/{id}` | владелец | правка, в том числе смена status |
| GET | `/vacancies` | Candidate | каталог active: `specialization`, `matchToMe`, `savedOnly`, P1 |
| GET | `/vacancies/{id}/match-to-me` | Candidate | CandidateMatch для себя, P1 |
| POST | `/vacancies/{id}/apply` | Candidate | отклик, `{ ok, message }`, P1 |
| GET/POST/DELETE | `/candidate/saved-vacancies[/{id}]` | Candidate | избранное, P1 |
| POST | `/vacancies/parse` | Employer | черновик вакансии из текста, P2 (NLP) |

Vacancy:

```json
{
  "id": "vac-1",
  "employerId": "user-emp-1",
  "companyName": "Resonance Labs",
  "title": "Frontend Engineer (React)",
  "description": "Развиваем продукт обратного рекрутинга",
  "specialization": "Frontend",
  "requiredGrade": "middle",
  "requiredSkills": ["React", "TypeScript"],
  "niceToHaveSkills": ["Jest", "Vite"],
  "salaryFrom": 260000,
  "salaryTo": 340000,
  "currency": "RUB",
  "city": "Москва",
  "workFormat": "remote",
  "extraInfo": null,
  "status": "active",
  "createdAt": "2026-09-01T10:00:00Z",
  "updatedAt": "2026-09-15T10:00:00Z"
}
```

Статусы: `draft`, `active`, `closed`, `archived`. Удаления фронтенд не делает, вакансию закрывают сменой статуса. Зарплатная вилка обязательна (ТЗ). Потребность работодателя — это вакансия, в том числе в статусе `draft`: отдельного `POST /matching/search` нет, подбор идёт через `GET /candidates?vacancyId=`. В каталоге кандидата приходит `VacancyWithMatch` = Vacancy + `match?`, `saved?`, `applied?`.

### Company API

| Метод | Endpoint | Доступ | Назначение |
|----|----|----|----|
| GET | `/employer/company` | Employer | профиль компании, фронт: нет |
| PUT | `/employer/company` | Employer | создать или обновить, фронт: нет |

ТЗ требует профиль компании (описание, направление, контакты), а фронтенд пока передаёт только строку `companyName` в вакансии и оффере. Backend хранит `companyName` как снимок в вакансии и оффере; если строка не пришла, подставляет название из профиля компании.

### Matching DTO

То, что фронтенд получает в `match`:

```json
{
  "candidateId": "6f0c2c1e-...",
  "vacancyId": "vac-1",
  "score": 85,
  "matchedSkills": ["React", "TypeScript", "Vite"],
  "missingInProfileSkills": ["Jest"],
  "reasons": [
    { "code": "SPECIALIZATION_MATCH", "label": "совпадает специализация Frontend", "positive": true },
    { "code": "GRADE_CONFIRMED", "label": "грейд middle подтверждён тестом", "positive": true },
    { "code": "TEST_SCORE", "label": "результат теста 82/100", "positive": true },
    { "code": "SKILLS_REQUIRED", "label": "указаны 2 из 2 обязательных навыков", "positive": true },
    { "code": "WORK_FORMAT_MATCH", "label": "подходит формат remote", "positive": true },
    { "code": "FSP_VERIFIED", "label": "подтверждённые достижения ФСП: 2", "positive": true }
  ],
  "relevantFsp": [
    { "id": "fsp-1", "title": "Кубок ФСП по веб-разработке", "placeOrResult": "2 место", "verified": true }
  ]
}
```

`missingInProfileSkills` означает «не указан в профиле», а не «кандидат не умеет». `relevantFsp` — до двух достижений ФСП, релевантных вакансии. Score в примере посчитан по текущей baseline-формуле (см. «Baseline matching»): 41 + 20,8 + 13,5 + 10 ≈ 85.

### Offer API

| Метод | Endpoint | Доступ | Назначение |
|----|----|----|----|
| POST | `/offers` | Employer | создать оффер |
| GET | `/candidate/offers` | Candidate | входящие |
| GET | `/employer/offers` | Employer | исходящие |
| GET | `/offers/{id}` | участники | детали; первое открытие кандидатом переводит `new` → `viewed` |
| POST | `/offers/{id}/accept` | Candidate | принять |
| POST | `/offers/{id}/decline` | Candidate | отклонить |

Создание:

```json
{
  "vacancyId": "vac-1",
  "candidateId": "6f0c2c1e-...",
  "companyName": "Resonance Labs",
  "positionTitle": "Frontend Engineer (React)",
  "salaryFrom": 280000,
  "salaryTo": 320000,
  "currency": "RUB",
  "workFormat": "remote",
  "message": "Нам близки ваш стек и опыт с ФСП. Готовы обсудить старт в ноябре."
}
```

Ответ `201` (так же выглядят элементы списков):

```json
{
  "id": "offer-1",
  "vacancyId": "vac-1",
  "candidateId": "6f0c2c1e-...",
  "employerId": "user-emp-1",
  "employerName": "Игорь Смирнов",
  "employerContact": { "type": "email", "value": "employer@demo.ru" },
  "companyName": "Resonance Labs",
  "positionTitle": "Frontend Engineer (React)",
  "salaryFrom": 280000,
  "salaryTo": 320000,
  "currency": "RUB",
  "workFormat": "remote",
  "message": "Нам близки ваш стек и опыт с ФСП. Готовы обсудить старт в ноябре.",
  "status": "new",
  "createdAt": "2026-10-05T14:00:00Z",
  "respondedAt": null
}
```

ТЗ требует, чтобы приглашение содержало способ связи. Фронтенд его не передаёт, поэтому Backend подставляет в `employerContact` email аккаунта работодателя. `employerName` и `employerContact` — дополнительные поля, фронтенд их пока не показывает. `accept` и `decline` возвращают обновлённый Offer.

### Shortlist, уведомления, дашборды, admin

| Метод | Endpoint | Доступ | Выход |
|----|----|----|----|
| GET | `/employer/shortlist` | Employer | CandidateProfile[], P1 |
| POST | `/employer/shortlist` | Employer | `{ candidateId }` → `{ ok: true }`, P1 |
| DELETE | `/employer/shortlist/{candidateId}` | Employer | 204, P1 |
| GET | `/notifications` | все роли | `{ items, unread }` |
| POST | `/notifications/{id}/read` | все роли | `{ ok: true }` |
| POST | `/notifications/read-all` | все роли | `{ ok: true }` |
| GET | `/dashboard/candidate` | Candidate | CandidateDashboard, P1 |
| GET | `/dashboard/employer` | Employer | EmployerDashboard, P1 |
| GET | `/dashboard/employer/analytics` | Employer | EmployerAnalytics, P1 |
| GET | `/admin/overview` | Admin | метрики |
| GET | `/admin/users` | Admin | пользователи со статусом |
| POST | `/admin/users/{id}/status` | Admin | `active` или `blocked` |
| GET | `/admin/offers`, `/admin/vacancies` | Admin | списки для модерации |

Уведомления Backend создаёт по событиям: `offer_new`, `offer_accepted`, `offer_declined`, `fsp_synced`, `application`, `system`. `profileViews` в дашборде кандидата считается по `profile_views`: запись появляется, когда работодатель открывает `GET /candidates/{id}`.

### Backend ↔ ML контракт

Backend не должен зависеть от конкретной реализации ML. Вызов пакетный: одна выдача — один вызов, `match-to-me` — пакет из одного кандидата. JSON — в том же camelCase.

```python
class Matcher(Protocol):
    async def rank(self, request: MatchingRequest) -> MatchingResponse:
        ...
```

Backend → ML:

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
      "testScore": 82,
      "skills": ["React", "TypeScript", "CSS", "Vite", "Redux"],
      "experienceYears": 4,
      "salaryFrom": 250000,
      "salaryTo": 320000,
      "workFormat": "remote",
      "fspAchievements": [
        { "id": "fsp-1", "title": "Кубок ФСП по веб-разработке", "discipline": "Продуктовое программирование", "placeOrResult": "2 место", "sportRank": "1 разряд", "verified": true },
        { "id": "fsp-2", "title": "Хакатон ФСП", "discipline": "Продуктовое программирование", "placeOrResult": "Финалист", "verified": true }
      ]
    }
  ]
}
```

ML → Backend:

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
        { "code": "FSP_VERIFIED", "params": { "count": 2 }, "positive": true }
      ],
      "components": { "test": 41, "skills": 20.8, "fsp": 13.5, "conditions": 10 }
    }
  ],
  "modelVersion": "baseline-v1"
}
```

ML возвращает коды причин с параметрами, текст `label` собирает Backend по словарю. `components` необязательны: они нужны для отладки и защиты, фронтенд их не получает. Если ML-сервис недоступен, Backend считает выдачу локальным `BaselineMatcher` по той же формуле: демо не должно зависеть от доступности сложной модели.

Словарь причин. `code` уникален в пределах списка: фронтенд использует его как React key.

| code | label |
|----|----|
| `SPECIALIZATION_MATCH` | совпадает специализация {specialization} |
| `GRADE_CONFIRMED` | грейд {grade} подтверждён тестом |
| `TEST_SCORE` | результат теста {score}/100 |
| `SKILLS_REQUIRED` | указаны {matched} из {total} обязательных навыков |
| `WORK_FORMAT_MATCH` | подходит формат {workFormat} |
| `WORK_FORMAT_MISMATCH` | формат кандидата: {workFormat} |
| `SALARY_MATCH` | ожидания кандидата в пределах вилки |
| `SALARY_MISMATCH` | ожидания кандидата выше вилки |
| `FSP_VERIFIED` | подтверждённые достижения ФСП: {count} |
| `FSP_RELEVANT` | достижение ФСП по дисциплине {discipline} |

### Чего не хватает во фронтенде

Backend поддерживает эти требования ТЗ, но во фронтенде для них пока нет экранов или полей:

- подтверждение email: баннер «подтвердите почту» и страница перехода по ссылке (`/auth/verify-email`);
- настройки приватности и согласия на обработку и публикацию данных (`/candidates/me/consents`);
- привязка ID участника ФСП (`PUT /candidates/me/fsp/link`): сейчас есть только синхронизация;
- телефон и Telegram в редактировании профиля: без них работодателю после accept раскроется только email;
- способ связи и имя менеджера в карточке оффера (`employerContact`, `employerName`);
- профиль компании (`/employer/company`);
- только рубли в формах вакансии, оффера и профиля: сейчас в селекте валюты есть `USD`;
- блок кода в вопросе теста (`code`);
- просмотр входящих откликов работодателем (P1): сейчас есть только уведомление `application`.

## Интеграция ФСП, тестирование и matching

### FSP Adapter

Поскольку реального API на хакатоне нет, не нужно придумывать его детали внутри бизнес-логики: ТЗ прямо говорит, что API и структура реестра намеренно не выдаются.

Нужен интерфейс:

```python
class FSPAdapter(Protocol):
    async def find_member(self, email: str, full_name: str) -> FSPMemberDTO | None:
        ...

    async def get_member(self, member_id: str) -> FSPMemberDTO:
        ...

    async def get_achievements(self, member_id: str) -> list[FSPAchievementDTO]:
        ...

    async def healthcheck(self) -> bool:
        ...
```

Нормализованная модель, из которой собирается `FspAchievement` для фронтенда:

```python
class FSPAchievementDTO(BaseModel):
    external_id: str
    title: str
    discipline: str | None
    achieved_at: date | None
    place_or_result: str | None      # "2 место", "Финалист", "Участник"
    participant_role: str | None
    sport_rank: str | None           # "1 разряд"
    achievement_type: Literal["participation", "finalist", "prize"]
    place: int | None
```

`achievement_type` и `place` Backend выводит из `place_or_result` и использует в FSP Signal, фронтенду они не нужны.

### Mock adapter

```text
app/
  integrations/
    fsp/
      base.py
      mock.py
      real.py
      fixtures/
        members.json
        achievements.json
```

Конфиг:

```env
FSP_PROVIDER=mock
```

или:

```env
FSP_PROVIDER=real
FSP_BASE_URL=...
FSP_API_TOKEN=...
```

### Real adapter

`RealFSPAdapter` должен существовать архитектурно, но до появления настоящей спецификации его задача ограничена:

```text
HTTP client
DTO validation
timeouts
normalization
error mapping
```

Нельзя делать остальную систему зависимой от неизвестного JSON ФСП.

### Контракт синхронизации

```text
Candidate
   ↓
POST /candidates/me/fsp/sync
   ↓
FSPService
   ↓
FSPAdapter
   ↓
normalize
   ↓
upsert achievements
   ↓
store snapshot
   ↓
response
```

Как находится участник. Фронтенд вызывает только синхронизацию, без привязки. Если `fsp_links` пуст, `MockFSPAdapter` ищет участника в mock-реестре по email аккаунта и ФИО и сохраняет найденный `fspMemberId`. Явная привязка — `PUT /candidates/me/fsp/link`. В реальной интеграции `fspMemberId` будет приходить из токена ФСП ID (Keycloak/OIDC), а не вводиться вручную: так подтверждается, что ID принадлежит этому человеку.

Успех:

```json
{
  "achievements": [
    {
      "id": "fsp-1",
      "title": "Кубок ФСП по веб-разработке",
      "discipline": "Продуктовое программирование",
      "date": "2025-11-10",
      "placeOrResult": "2 место",
      "participantRole": "Участник",
      "sportRank": "1 разряд",
      "verified": true
    }
  ],
  "syncedAt": "2026-10-07T14:00:00Z",
  "status": "synced"
}
```

Нет истории:

```json
{
  "achievements": [],
  "syncedAt": "2026-10-07T14:00:00Z",
  "status": "no_history"
}
```

Это HTTP 200, не ошибка. Отсутствие спортивной истории не должно блокировать создание профиля или подбор кандидата: это отдельно зафиксировано в ТЗ.

Кэш и fallback — в PostgreSQL:

```text
fsp_links.last_synced_at
fsp_links.raw_snapshot JSONB
fsp_achievements
```

Допущение: TTL свежего snapshot = 24 часа.

| Ситуация | Backend |
|----|----|
| ФСП работает | синхронизирует, `status = synced` |
| ФСП timeout, есть кэш | 200, кэш и `status = stale` |
| ФСП timeout, кэша нет | 503 `FSP_UNAVAILABLE` |
| Участник не найден при привязке | 404 `FSP_MEMBER_NOT_FOUND` |
| Участник найден, достижений нет | 200, `status = no_history` |
| Одно достижение пришло повторно | upsert |
| FSP ID уже привязан другому аккаунту | 409 `FSP_ID_ALREADY_LINKED` |

Допущение: timeout внешнего API = 2 секунды и максимум 1 retry. Больше для интерактивного запроса на хакатоне не нужно.

### Механика тестирования

Это нельзя выкидывать из Backend P0: в актуальном ТЗ тестирование, валидация и категоризация дают ещё 25% оценки. 

При этом не надо за четыре дня создавать LeetCode.

**Почему не статический банк вопросов.** Если тест собирается из фиксированного пула с готовыми ответами, пул быстро утекает между кандидатами: ТЗ прямо называет единый набор заданий неподходящим, а генерацию заданий нейросетью — не гарантирующей сопоставимую сложность. Поэтому основная единица банка — не вопрос, а **шаблон вопроса**.

Шаблон задаёт структуру задачи и диапазоны параметров. Конкретные значения генерируются под каждую попытку, правильный ответ вычисляет код генератора, а не хранится в банке:

```text
template: sql_join_count
topic: databases | difficulty: 2 | grade: middle

params:
  users: random_rows(5..8)
  orders: random_rows(6..10, fk=users)
  join: choice(INNER, LEFT)

prompt: |
  Сколько строк вернёт запрос?
  SELECT * FROM users u {join} JOIN orders o ON o.user_id = u.id

answer: eval_sql(params)    # вычисляется кодом
distractors: answer±1, rows(users), rows(orders)
```

Сложность задаётся структурой шаблона (размер таблиц, глубина вложенности, число шагов), а не конкретными значениями. Поэтому два кандидата получают разные задачи одной сложности, а утёкший экземпляр бесполезен: у следующего кандидата другие данные и другой правильный ответ.

Рабочий pipeline:

```text
specialization + requested grade
        ↓
test blueprint (темы × сложность)
        ↓
для каждого слота — случайный шаблон темы
        ↓
generator(seed) → prompt, options, correct
        ↓
экземпляр сохраняется в test_session_items
        ↓
server-side scoring
        ↓
confirmed category
```

Например, blueprint для Backend Middle:

```text
HTTP/API            2 вопроса
Databases           2
Python/backend      3
Algorithms          1
Architecture        2
-------------------------
Итого              10
```

Банк содержит элементы двух типов:

- **generated** — SQL, вывод кода Python/JS, сложность алгоритма, порядок event loop, специфичность CSS, regex. Каждый показ — новый экземпляр.
- **static** — темы, которые не шаблонизируются: архитектура, HTTP-семантика, практики. Пул вариантов с exposure control: вопрос выводится из оборота после `STATIC_ITEM_MAX_EXPOSURES` показов.

Допущение: доля static-вопросов в одном тесте не больше 40%, то есть в тесте из 10 вопросов минимум 6 сгенерированных: в blueprint Backend Middle static — Architecture и часть HTTP/API. Варианты ответа всегда перемешиваются.

Генераторы живут в коде:

```text
app/
  testing/
    blueprints.py
    generators/
      base.py            # Generator protocol + registry
      sql_join_count.py
      python_output.py
      big_o.py
      js_event_loop.py
      css_specificity.py
    static_pool/
      backend.yaml
      frontend.yaml
```

```python
class Generator(Protocol):
    template_id: str
    topic: str
    difficulty: int

    def generate(self, rng: random.Random) -> QuestionInstance:
        ...


class QuestionInstance(BaseModel):
    text: str
    code: str | None
    options: list[Option]       # уже перемешаны
    correct_option_id: str      # никогда не уходит на frontend
```

Seed берётся из `secrets.randbits(64)` и сохраняется в `test_session_items`, поэтому любую выданную задачу можно воспроизвести при разборе спорного результата.

Генераторы покрываются тестами: для каждого шаблона прогоняем 1000 seed и проверяем, что правильный ответ совпадает с независимым вычислением (например, реальным запросом в SQLite), варианты ответа не повторяются, а параметры остаются в заданных диапазонах.

Допущение для MVP: 6–8 шаблонов на Backend и столько же на Frontend, покрывающих все темы blueprint. Остальные специализации из справочника на старте работают на static-пуле.

**Тест под стек и вакансию.** ТЗ просит показать, как система формирует задания на основе описаний вакансий. Blueprint задаёт темы и сложность для категории, а `stack` из `POST /tests/sessions` и `requiredSkills` вакансий выбирают шаблоны внутри темы по тегам:

```text
blueprint Frontend Middle: JS 3, React 3, HTTP/API 2, Architecture 2
stack = [React, TypeScript]
        ↓
слоты JS и React берут шаблоны с тегами react, typescript
        ↓
число слотов и сложность не меняются → результаты сопоставимы
```

Для демо готовим 3–4 описания вакансий и показываем цепочку: вакансия → `requiredSkills` → теги шаблонов → собранный тест. Кандидат проходит тест на категорию один раз, а не под каждую вакансию: стек меняет только темы внутри слотов.

**Допущение:** проходной балл = 70/100.

**Допущение по смене грейда:** успешное изменение подтверждённого грейда возможно не чаще одного раза в 90 дней. Неуспешная попытка не запускает cooldown и позволяет сразу попробовать уровень ниже. Само ТЗ требует ограничивать частоту изменения грейда и приводит три месяца как пример. 

### Категоризация

Категория:

```text
specialization + confirmedGrade
```

Например:

```text
Frontend + middle
Backend + junior
Data Science + middle
```

Специализацию кандидат выбирает сам (профиль и старт теста), грейд подтверждает только тест. ТЗ прямо говорит, что выдача должна формироваться на основании категории, полученной через опрос и тестирование, а не самоописанного резюме. ML-категоризация по навыкам (ML-02) в контракт подбора не входит и может использоваться как подсказка при выборе специализации.

### Baseline matching

Сначала hard filters при подборе под вакансию (`GET /candidates?vacancyId=`):

```text
candidate.specialization = vacancy.specialization
candidate.confirmedGrade = vacancy.requiredGrade
candidate.readiness ≠ not_looking
email кандидата подтверждён
аккаунт не заблокирован
```

Кандидат без подтверждённого грейда в подбор под вакансию не попадает, но виден в общем каталоге без `vacancyId`.

После этого score. Для MVP предлагаю:

```text
Match Score =
50% Test Score
25% Skills Match
15% FSP Signal
10% Conditions Match
```

Почему так: категория уже является hard gate, поэтому повторно давать очки за специализацию нет смысла. Главный вес получает объективный результат теста, затем технологический fit, потом подтверждённые данные ФСП. Веса ещё не согласованы с ML-документом (там 40 / 25 / 15 / 10 / 10) — это открытое решение команды.

Формально:

```text
score =
0.50 × test_score
+
0.25 × skill_match
+
0.15 × fsp_signal
+
0.10 × conditions_match
```

### Skills Match

Required skill:

```text
weight = 2
```

Optional:

```text
weight = 1
```

Формула:

```text
skill_match =
100 × matched_weight / total_weight
```

Например:

```text
Required:
Python ✓     2
FastAPI ✓    2
PostgreSQL ✓ 2

Optional:
Docker ✗     1

matched = 6
total = 7

Skills Match = 85.7
```

### FSP Signal

Это не оценка профессионального уровня, а дополнительный ranking signal.

Для синтетического MVP каждое достижение даёт баллы по типу, спортивный разряд добавляется один раз:

```text
participation (участие)         +10
finalist (финал)                +20
prize (призовое место)          +30
sportRank (спортивный разряд)   +40, один раз
```

Сумма ограничивается:

```text
fsp_signal <= 100
```

Все коэффициенты выносятся в конфиг:

```python
FSP_WEIGHTS = {
    "participation": 10,
    "finalist": 20,
    "prize": 30,
}
FSP_SPORT_RANK_BONUS = 40
```

Когда появится реальная структура ФСП, mapping можно заменить.

### Conditions Match

Например:

```text
work format   50%
salary        50%
```

Если salary expectation кандидата отсутствует:

```text
salary component = neutral 50
```

а не 0.

### Explainability

Matcher обязан вернуть причины. Не:

```json
{
  "score": 85
}
```

а:

```json
{
  "score": 85,
  "reasons": [
    { "code": "TEST_SCORE", "label": "результат теста 82/100", "positive": true },
    { "code": "SKILLS_REQUIRED", "label": "указаны 2 из 2 обязательных навыков", "positive": true },
    { "code": "FSP_VERIFIED", "label": "подтверждённые достижения ФСП: 2", "positive": true }
  ]
}
```

Причины с `positive: false` фронтенд показывает как минус, например `WORK_FORMAT_MISMATCH`. Объяснимость подборки прямо входит в требования и критерии оценки конкурса.

## Офферы, бизнес-правила и обработка ошибок

### State machine приглашения

Статусы — как во фронтенде:

```text
new
 ↓  кандидат открыл GET /offers/{id}
viewed
 ↙        ↘
accepted   declined
```

Terminal states: `accepted`, `declined`. Отзыв оффера работодателем (`withdrawn`) — P1: во фронтенде его нет.

### Создание оффера

Backend принимает приглашение, только если:

- у пользователя роль employer и подтверждён email;
- кандидат существует и не заблокирован;
- `readiness` кандидата не `not_looking`;
- `salaryFrom > 0` и `salaryTo >= salaryFrom`;
- `currency = RUB`;
- при наличии `vacancyId` вакансия принадлежит этому работодателю и не в статусе `closed` или `archived`;
- у работодателя нет другого активного (`new` или `viewed`) оффера этому кандидату по той же вакансии, а для оффера без вакансии — другого активного оффера без вакансии.

При нарушении — `409 OFFER_ALREADY_EXISTS`, `409 CANDIDATE_NOT_AVAILABLE` или `409 VACANCY_CLOSED`.

### Обязательные поля оффера

```text
candidateId
companyName
positionTitle
message
salaryFrom
salaryTo
currency = RUB
workFormat
```

`vacancyId` необязателен. `employerContact` Backend заполняет сам email аккаунта работодателя, если он не передан. ТЗ требует, чтобы кандидат видел зарплату до начала общения, а приглашение содержало компанию, предложение, зарплату и способ связи.

### Раскрытие контактов

Критичное правило выполняется на Backend, а не скрытием на фронте. Контакты отдаёт один метод — `GET /candidates/{id}/contacts`, и только если:

- кандидат принял оффер этого работодателя (`accepted`), или
- кандидат сам откликнулся на вакансию этого работодателя (P1).

До этого:

```json
GET /api/candidates/6f0c2c1e-.../contacts
403
{
  "message": "Контакты доступны после принятия предложения",
  "code": "CONTACTS_LOCKED"
}
```

После `POST /offers/{id}/accept`:

```json
{
  "email": "anna.kovaleva@demo.ru",
  "phone": "+7 999 111-22-33",
  "telegram": "@anna_front"
}
```

`email` берётся из аккаунта, `phone` и `telegram` — из профиля. Для демо используются синтетические контакты. Каждое успешное раскрытие пишется в audit как `CONTACTS_REVEALED`.

### Защита от гонок

Если фронтенд дважды отправил accept, второй запрос не должен повторно менять состояние. В транзакции:

```sql
UPDATE offers
SET status = 'accepted', responded_at = now()
WHERE id = :id
  AND candidate_id = :candidate_id
  AND status IN ('new', 'viewed');
```

Если `updated_rows = 0` — `409 INVALID_OFFER_STATE`. Фронтенд допускает optimistic UI на accept и decline и откатывает его при ошибке.

### CRUD и бизнес-права

Candidate:

```text
Create    автоматически при регистрации
Read      кандидат сам / employer без контактов
Update    только владелец
Delete    владелец или admin
```

Company:

```text
Create/Update    employer, один профиль на аккаунт
Read             все авторизованные
```

Vacancy:

```text
Create    employer
Read      active — все авторизованные, draft — только владелец
Update    владелец, включая смену status
Delete    нет: закрытие через status closed / archived
```

Skills:

```text
Read      все
Create    admin; неизвестный навык из профиля или вакансии добавляется автоматически
Update    admin
Delete    admin
```

FSP achievements:

```text
Read      candidate + employer
Create    только интеграция / admin seed
Update    интеграция / admin
Delete    интеграция / admin
```

Кандидат не может вручную редактировать подтверждённое достижение ФСП.

### Edge cases

| Ситуация | HTTP | code | Поведение |
|----|----|----|----|
| Email уже занят | 409 | `EMAIL_ALREADY_EXISTS` | не создавать user |
| Email не подтверждён | 403 | `EMAIL_NOT_VERIFIED` | логин разрешён; нельзя отправлять офферы, кандидат скрыт из Talent Pool |
| Неверный пароль | 401 | `INVALID_CREDENTIALS` | без уточнения, существует ли email |
| Аккаунт заблокирован | 403 | `USER_BLOCKED` | вход запрещён |
| Токен истёк или сессия отозвана | 401 | `TOKEN_EXPIRED` | фронтенд разлогинивает |
| Не та роль | 403 | `FORBIDDEN_ROLE` | отказ |
| Профиль не заполнен | 409 | `PROFILE_INCOMPLETE` | вернуть недостающие поля |
| FSP ID уже используется | 409 | `FSP_ID_ALREADY_LINKED` | не связывать |
| Участник ФСП не найден | 404 | `FSP_MEMBER_NOT_FOUND` | не связывать |
| Истории ФСП нет | 200 | `status=no_history` | нормальный профиль |
| ФСП timeout, есть кэш | 200 | `status=stale` | вернуть кэш |
| ФСП timeout, кэша нет | 503 | `FSP_UNAVAILABLE` | повторить позже |
| Сессия теста уже завершена | 409 | `TEST_SESSION_COMPLETED` | результат не пересчитывать |
| Сессия теста истекла | 409 | `TEST_SESSION_EXPIRED` | начать новую |
| Слишком ранняя смена грейда | 409 | `GRADE_CHANGE_COOLDOWN` | вернуть `details.nextAvailableAt` |
| Вилка `salaryFrom > salaryTo` | 422 | `INVALID_SALARY_RANGE` | ошибка валидации |
| Зарплата не указана | 422 | `SALARY_REQUIRED` | не создавать |
| Валюта не RUB | 422 | `CURRENCY_NOT_SUPPORTED` | не создавать |
| Кандидат `not_looking` | 409 | `CANDIDATE_NOT_AVAILABLE` | не отправлять |
| Оффер уже принят или отклонён | 409 | `INVALID_OFFER_STATE` | идемпотентная обработка |
| Контакты запрошены раньше accept | 403 | `CONTACTS_LOCKED` | не отдавать PII |
| Вакансия закрыта | 409 | `VACANCY_CLOSED` | оффер по ней не создавать |
| Кандидат не найден | 404 | `CANDIDATE_NOT_FOUND` |    |
| Нет результатов подбора | 200 | `items=[]` | это не ошибка |
| ML недоступен | 200 | — | fallback на `BaselineMatcher` |

### HTTP validation

Для ошибок схемы используется `422`, но в том же плоском формате, что и бизнес-ошибки: фронтенд читает только `message`, а `code` нужен, чтобы не разбирать русские тексты.

```json
{
  "message": "Для приглашения необходимо указать зарплатную вилку",
  "code": "SALARY_REQUIRED",
  "details": { "field": "salaryFrom" },
  "requestId": "req-0199"
}
```

## NFR, тестирование, миграции и развёртывание

### Производительность

ТЗ ожидает устойчивую работу для десятков одновременных пользователей и приемлемое время поиска, открытия профиля и формирования подборки.

Для команды я бы превратил это в конкретные hackathon SLO.

**Допущение, ориентиры MVP:**

| Операция | Target P95 |
|----|---:|
| `/auth/me` | < 200 ms |
| Профиль кандидата | < 300 ms |
| CRUD vacancy/company | < 400 ms |
| Поиск кандидатов без matching | < 500 ms |
| Matching до 1000 кандидатов | < 800 ms |
| Offer create/accept | < 400 ms |
| FSP Mock sync | < 500 ms |
| Real FSP sync | < 3.5 sec |

Это **не production SLA**, а критерий готовности демо.

Для MVP:

```text
limit <= 50
default limit = 20
```

Обязательно pagination.

Не нужны:

```text
Elasticsearch
Kafka
Redis
Kubernetes
```

при объёме синтетических данных хакатона.

### Безопасность

Минимальный набор:

- HTTPS на публичном стенде;
- хеширование паролей Argon2id;
- проверка подписи JWT, `exp`, `sub`, `sid`, `role` и отзыва сессии;
- access token на 8 часов (фронтенд не умеет refresh), refresh с ротацией — P1;
- токен передаётся только в заголовке `Authorization`, cookie не используются, поэтому CSRF-защита не нужна;
- CORS только для домена фронтенда либо same-origin через прокси `/api`;
- rate limiting (slowapi): логин и регистрация — 5 запросов в минуту с IP, повторная отправка письма — 1 в минуту, офферы — 50 в сутки на работодателя;
- secrets через environment variables, никакого `SECRET_KEY` в git;
- проверка RBAC и владения объектом на каждом защищённом endpoint;
- контакты кандидата никогда не входят в DTO работодателя, кроме `GET /candidates/{id}/contacts`;
- не писать в логи пароль, JWT, телефон и email.

### Персональные данные и 152-ФЗ

Актуальное ТЗ прямо требует согласия на обработку и публикацию профиля, разграничения ролей и безопасного хранения паролей и токенов.

Для MVP Backend должен как минимум хранить:

```text
CONSENT_PERSONAL_DATA
CONSENT_PROFILE_PUBLICATION
CONSENT_FSP_SYNC
```

Пример:

```json
{
  "type": "profile_publication",
  "version": "2026-10-01",
  "acceptedAt": "2026-10-07T10:00:00Z"
}
```

Роскомнадзор указывает, что владелец интернет-сервиса, собирающий данные, позволяющие прямо или косвенно определить человека, фактически выступает оператором персональных данных; для production этим не исчерпываются юридические обязанности оператора.

Поэтому для хакатона разумный минимум:

```text
consent
+
data minimization
+
role isolation
+
PII not in logs
+
TLS
+
controlled disclosure
```

Полноценное production-соответствие 152-ФЗ уже требует отдельного юридического и инфраструктурного аудита, его не стоит изображать выполненным только потому, что в интерфейсе есть checkbox.

### Логирование

Структурированный JSON:

```json
{
  "timestamp": "...",
  "level": "INFO",
  "request_id": "req-123",
  "user_id": "user-123",
  "route": "/api/offers",
  "method": "POST",
  "status": 201,
  "duration_ms": 84
}
```

Не логировать:

```text
password
access_token
refresh_token
full request body offers/profile
phone
email
FSP raw payload с PII
```

### Audit

Отдельные audit events:

```text
USER_REGISTERED
EMAIL_VERIFIED
FSP_LINKED
FSP_SYNCED
TEST_FINISHED
GRADE_CONFIRMED
VACANCY_CREATED
MATCH_REQUESTED
OFFER_SENT
OFFER_ACCEPTED
OFFER_DECLINED
CONTACTS_REVEALED
```

Пример:

```json
{
  "action": "CONTACTS_REVEALED",
  "actor_user_id": "employer-1",
  "entity_type": "offer",
  "entity_id": "offer-1",
  "metadata": {
    "candidate_id": "candidate-1"
  }
}
```

Сами контакты в audit metadata не кладём.

### Тесты Backend

FastAPI предоставляет `TestClient`, работающий через HTTPX и интегрируемый с pytest, поэтому для MVP не нужно придумывать отдельный testing framework.

**Unit tests P0:**

```text
test_password_hash
test_jwt_expiration
test_rbac_candidate
test_rbac_employer

test_generators_correctness
test_static_exposure_limit
test_test_scoring
test_test_pass_threshold
test_grade_cooldown

test_skill_match
test_fsp_signal
test_match_total
test_missing_in_profile_skills
test_explainability

test_offer_transitions
test_salary_validation
test_contacts_locked
test_contacts_unlock_after_accept

test_fsp_normalizer
test_fsp_no_history
test_error_format_flat
test_camel_case_aliases
```

**Integration tests P0:**

```text
register → verify → login

candidate profile → skills

test session → answer → finish → category

FSP sync без привязки и с привязкой

employer → vacancy

GET /candidates?vacancyId → ranked candidates

offer → candidate receives

accept → contacts unlocked
```

Контрактная проверка: из `/api/openapi.json` генерируются TypeScript-типы (`openapi-typescript`) и в CI сравниваются с `src/entities/types.ts` фронтенда. Так расхождение имён и полей ловится до демо, а не на нём.

То есть один обязательный smoke test должен проходить весь golden path:

```text
Candidate
  ↓
Test
  ↓
Category
  ↓
FSP
  ↓
Employer Search
  ↓
Match
  ↓
Offer
  ↓
Accept
  ↓
Contacts
```

### Validation matching

Поскольку организаторы не предоставляют готовый датасет или эталонную разметку, ТЗ требует команде предложить собственную процедуру проверки качества.

Минимально:

```text
5 тестовых вакансий
×
10 кандидатов
=
50 candidate-vacancy pairs
```

PM вручную размечает:

```text
relevant
not relevant
```

Дальше считаем:

```text
Precision@3
Precision@5
```

Например:

```text
Vacancy: Backend Middle

Эксперт считает релевантными:
A, B, C, D

TOP-5 matcher:
A, B, X, C, D

Precision@5 = 4/5 = 0.80
```

Этого достаточно, чтобы на защите не говорить только:

> кажется, matching работает хорошо.

### Seed для демо

Команда должна получать готовый продукт командой:

```bash
python -m app.seed
```

Создать:

```text
1 admin
2 employer accounts
2 companies
5 vacancies / needs

10-15 candidate accounts
7 specializations
5 grades
20-30 skills с синонимами

12-16 question templates (Backend, Frontend)
30-40 static questions
10-15 test sessions

20-30 FSP achievements
5 кандидатов без FSP history

5-10 offers разных статусов
```

Демо-аккаунты совпадают с фикстурами фронтенда (`src/mocks/fixtures.ts`), чтобы его демо-логины работали и с настоящим Backend. Пароль `demo1234` — только для демо-стенда:

```text
candidate@demo.ru    candidate   Анна Ковалёва, Frontend middle
employer@demo.ru     employer    Игорь Смирнов, Resonance Labs
admin@demo.ru        admin
```

Обязательно иметь пару кандидатов, на которой видно, что ranking учитывает несколько сигналов, а не сортирует по одному числу. Для вакансии Frontend middle (React, TypeScript, remote):

```text
Кандидат A: тест 82, React / TypeScript / Vite, ФСП: 2 место + разряд, remote  → ≈ 85
Кандидат B: тест 91, React / JavaScript, без ФСП, office                      → ≈ 59
```

### Минимальные миграции

Я бы не создавал 15 мелких Alembic migrations за 4 дня. Достаточно четырёх осмысленных.

Migration `auth_and_taxonomy`:

```text
users
auth_sessions
email_verification_tokens

specializations
grades
skills
```

Migration `candidate_and_tests`:

```text
candidate_profiles
candidate_skills

question_templates
test_sessions
test_session_items

consents
```

Migration `employer_and_vacancies`:

```text
companies
vacancies
vacancy_skills
```

Migration `fsp_offers_engagement`:

```text
fsp_links
fsp_achievements
offers
applications
shortlist_items
saved_vacancies
notifications
profile_views
audit_events
indexes
```

Все изменения БД идут через Alembic migrations, а не через ручные `CREATE TABLE` на сервере.

Минимальные SQL constraints:

```sql
CHECK (salary_from IS NULL OR salary_from > 0)

CHECK (
    salary_to IS NULL
    OR salary_from IS NULL
    OR salary_to >= salary_from
)

CHECK (currency = 'RUB')

CHECK (readiness IN ('actively_looking', 'open_to_offers', 'not_looking'))

CHECK (work_format IN ('remote', 'hybrid', 'office'))

UNIQUE (candidate_id, source, external_id)

UNIQUE (candidate_id, skill_id)

UNIQUE (vacancy_id, skill_id)

UNIQUE (fsp_member_id)
```

Для users:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(320) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(32) NOT NULL
        CHECK (role IN ('candidate', 'employer', 'admin')),
    display_name VARCHAR(255) NOT NULL,
    email_verified_at TIMESTAMPTZ NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX ux_users_email
ON users (lower(email));
```

Для offers:

```sql
CREATE TABLE offers (
    id UUID PRIMARY KEY,
    employer_id UUID NOT NULL REFERENCES users(id),
    candidate_id UUID NOT NULL REFERENCES candidate_profiles(id),
    vacancy_id UUID NULL REFERENCES vacancies(id),

    company_name VARCHAR(255) NOT NULL,
    position_title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,

    salary_from INTEGER NOT NULL,
    salary_to INTEGER NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'RUB',
    work_format VARCHAR(16) NOT NULL,
    employer_contact JSONB NOT NULL,

    status VARCHAR(16) NOT NULL DEFAULT 'new'
        CHECK (status IN ('new', 'viewed', 'accepted', 'declined')),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    viewed_at TIMESTAMPTZ NULL,
    responded_at TIMESTAMPTZ NULL,

    CHECK (salary_from > 0),
    CHECK (salary_to >= salary_from),
    CHECK (currency = 'RUB'),
    CHECK (work_format IN ('remote', 'hybrid', 'office'))
);
```

### Deployment

Минимальная структура:

```text
backend/
  app/
  alembic/
  tests/
  Dockerfile
  pyproject.toml

frontend/
  ...

compose.yaml
.env.example
README.md
```

`compose.yaml`:

```text
frontend    nginx: статика + прокси /api → backend
backend
postgres
mailpit     SMTP для писем подтверждения, веб-интерфейс :8025
ml          optional
```

Фронтенд собирается с `VITE_USE_MOCKS=false` и `VITE_API_BASE_URL=/api`. Nginx отдаёт статику и проксирует `/api` на backend, поэтому фронтенд и API живут на одном origin и CORS не нужен. На публичном стенде вместо Mailpit нужен настоящий SMTP (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` в env): жюри должно получить письмо подтверждения на свою почту.

Запуск:

```bash
docker compose up -d --build
```

Миграции:

```bash
docker compose exec backend alembic upgrade head
```

Seed:

```bash
docker compose exec backend python -m app.seed
```

Проверка:

```text
GET /api/health/live
GET /api/health/ready
```

Swagger и OpenAPI:

```text
/api/docs
/api/openapi.json
```

FastAPI по умолчанию даёт OpenAPI и Swagger UI, что закрывает обязательное требование ТЗ документировать endpoints, запросы, ответы и ошибки.

`/api/health/live`:

```json
{
  "status": "ok"
}
```

`/api/health/ready`:

```json
{
  "status": "ok",
  "database": "ok",
  "fspProvider": "mock",
  "matcher": "baseline"
}
```

ФСП не должен переводить readiness приложения в DOWN, если доступен сохранённый snapshot или используется mock: внешний источник не должен уронить весь сервис.

## Дорожная карта Backend на четыре дня

Здесь важно идти не слоями типа сначала вся БД, потом весь API, потом интеграция. Делайте **вертикальный сценарий**, который можно показать уже в середине хакатона.

### День первый: фундамент

Цель дня: фронтенд переключается с MSW на настоящий API хотя бы для auth и профиля.

Backend делает:

```text
FastAPI project
PostgreSQL
SQLAlchemy
Alembic
Pydantic schemas с camelCase-алиасами
единый формат ошибок
Dockerfile
compose.yaml
```

Далее:

```text
users
auth_sessions
candidate_profiles
specializations
grades
skills
```

Endpoints:

```text
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
POST /auth/verify-email

GET/PATCH /candidates/me

GET /specializations
GET /grades
GET /skills
```

К концу дня есть Swagger, а схемы сверены с `src/entities/types.ts`.

Definition of Done:

```text
register
→ login
→ candidate profile
```

работают через API с фронтендом без MSW.

### День второй: тестирование + ФСП

С утра:

```text
question_templates
test_sessions
test_session_items
генераторы шаблонов
```

Endpoints:

```text
POST /tests/sessions
GET  /tests/sessions/{id}/question
POST /tests/sessions/{id}/answer
POST /tests/sessions/{id}/finish
GET  /tests/sessions/{id}/result
GET  /tests/history
```

Результат:

```text
Candidate
→ specialization
→ claimedGrade
→ test session
→ confirmed category
```

После этого:

```text
FSPAdapter
MockFSPAdapter
RealFSPAdapter interface

fsp_links
fsp_achievements
```

Endpoints:

```text
POST /candidates/me/fsp/sync
GET  /candidates/me/fsp/achievements
GET  /candidates/{id}/fsp/achievements
PUT  /candidates/me/fsp/link
```

К вечеру профиль кандидата должен полностью формироваться.

### День третий: главный конкурсный сценарий

Сначала:

```text
companies
vacancies
vacancy_skills

POST /employer/vacancies
GET  /employer/vacancies
GET/PATCH /vacancies/{id}
```

Затем подбор:

```text
GET /candidates?vacancyId=...
GET /candidates/{id}
```

Backend и ML к этому моменту должны иметь стабильный контракт. Сначала обязательно реализовать `BaselineMatcher` и только потом подключать ML.

После matching:

```text
offers

POST /offers
GET  /candidate/offers
GET  /employer/offers
GET  /offers/{id}
POST /offers/{id}/accept
POST /offers/{id}/decline
GET  /candidates/{id}/contacts
```

Definition of Done третьего дня:

```text
Employer
   ↓
вакансия Frontend middle
   ↓
Talent Pool с match и причинами
   ↓
open candidate
   ↓
send offer 280-320k
   ↓
Candidate receives
   ↓
Accept
   ↓
Contacts unlocked
```

Если это работает, у команды уже есть продукт для защиты. Это тот же happy path, что в DoD фронтенда (`p0.dod.test.ts`).

### День четвёртый: никаких больших новых фич

Backend:

```text
integration tests
error handling
indexes
audit
seed data
logging
healthcheck
Docker
Swagger descriptions
README
deployment
```

ML + Backend:

```text
5 вакансий
×
10 кандидатов
```

считают validation metrics.

После этого только багфиксы.

**P1, только если P0 стабилен:**

- классический отклик кандидата, shortlist, уведомления, дашборды и избранные вакансии (во фронтенде уже готовы);
- регулярные короткие задания;
- PDF resume parser;
- PDF generation;
- admin CRUD;
- employer verification;
- moderation;
- ATS integration.

**Не трогать на 4-дневном MVP:**

```text
Kafka
Kubernetes
Elasticsearch
сложный event bus
Redis без реальной необходимости
10 микросервисов
полноценную ATS
production Keycloak
real-time WebSocket chat
```

Модульный монолит полностью допустим актуальным ТЗ, если frontend, backend и storage логически разделены.

---

## Что делать прямо сейчас, первые пять шагов команды

**Первое. Сверить контракт с фронтендом, а не придумывать его заново.** Фронтенд уже написан: типы в `src/entities/types.ts`, пути в `src/shared/api/endpoints.ts`, поведение в `src/mocks/handlers.ts`. Backend повторяет их в Pydantic-схемах. Особенно важен `match`:

```json
{
  "score": 85,
  "matchedSkills": [],
  "missingInProfileSkills": [],
  "reasons": [{ "code": "TEST_SCORE", "label": "результат теста 82/100", "positive": true }]
}
```

После этого менять названия полей только осознанно и вместе с фронтендом.

**Второе. Backend сразу создаёт первые Alembic migrations и seed.** Не начинать с 25 endpoints. Сначала:

```text
users
candidate_profiles
skills
specializations
grades
```

и демо-кандидат `candidate@demo.ru` должен читаться через `GET /api/candidates/me`.

**Третье. ML и Backend сегодня же фиксируют контракт Matcher.** ML получает вакансию и пакет кандидатов и возвращает:

```text
score
matchedSkills
missingInProfileSkills
reasons (code + params + positive)
components (необязательно)
```

Backend одновременно пишет `BaselineMatcher`, чтобы проект работал даже без готовой ML-модели.

**Четвёртое. Сразу сделать FSP Mock Adapter, не ждать реального API.** ТЗ специально не предоставляет API ФСП, поэтому ожидание интеграции только потеряет время. К вечеру должен работать `POST /candidates/me/fsp/sync` с тремя кейсами:

```text
есть достижения
нет достижений
ошибка источника
```

**Пятое. Создать один automated golden-path test и больше его не ломать.** Он должен проверять:

```text
register candidate
→ verify email
→ fill profile
→ test session → finish
→ FSP sync

register employer
→ verify email
→ create vacancy
→ GET /candidates?vacancyId=...
→ send offer

candidate
→ accept offer

employer
→ GET /candidates/{id}/contacts
```

Если этот тест зелёный к концу третьего дня, команда может спокойно выходить на защиту. Все остальные возможности уже являются улучшением основной механики, а не условием того, что продукт вообще существует.