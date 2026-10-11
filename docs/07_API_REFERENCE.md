# 07. Справочник API

Базовый префикс: **/api**.  
Интерактивная документация (Swagger UI): после запуска стенда откройте путь `/api/docs` на том же хосте, что и Backend (напрямую порт 8000 или через nginx порт 8080).  
Машина OpenAPI: `/api/openapi.json`.

Формат ошибки:

```json
{
  "message": "Контакты доступны после принятия предложения",
  "code": "CONTACTS_LOCKED",
  "details": {},
  "requestId": "req_…"
}
```

Авторизация защищённых методов: заголовок `Authorization: Bearer <accessToken>`.  
JSON — camelCase (Pydantic aliases).

Ниже — сводка по группам из реальных роутеров `backend/app/api/routes/`. Полные схемы полей смотрите в Swagger и `backend/app/schemas/`.

---

## 1. Health

| Метод | Путь | Роль | Назначение |
| ----- | ---- | ---- | ---------- |
| GET | `/api/health/live` | публично | liveness |
| GET | `/api/health/ready` | публично | readiness (БД) |

Пример:

```bash
curl -s http://localhost:8000/api/health/ready
```

---

## 2. Auth

| Метод | Путь | Роль | Назначение |
| ----- | ---- | ---- | ---------- |
| POST | `/api/auth/register` | публично | регистрация |
| POST | `/api/auth/login` | публично | вход |
| POST | `/api/auth/refresh` | cookie refresh | ротация |
| POST | `/api/auth/logout` | user | выход |
| GET | `/api/auth/me` | user | текущий пользователь |
| POST | `/api/auth/verify-email` | публично | подтверждение JSON |
| POST | `/api/auth/resend-verification` | user | повтор письма |
| GET/POST | `/api/auth/verify-email/confirm` | публично | HTML из письма |

Пример логина:

```bash
curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"employer@demo.ru","password":"demo1234"}'
```

Бизнес-правила: неподтверждённый email не блокирует login; блокирует офферы работодателя и попадание кандидата в Talent Pool.

---

## 3. Taxonomy

| Метод | Путь | Назначение |
| ----- | ---- | ---------- |
| GET | `/api/specializations` | список |
| GET | `/api/grades` | грейды по rank |
| GET | `/api/skills?q=` | поиск навыков |

---

## 4. Candidate profile / FSP / passport

| Метод | Путь | Роль |
| ----- | ---- | ---- |
| GET/PATCH/DELETE | `/api/candidates/me` | candidate |
| GET | `/api/candidates/me/completeness` | candidate |
| GET/PUT | `/api/candidates/me/consents` | candidate |
| GET | `/api/candidates/me/passport` | candidate |
| GET | `/api/candidates/me/fsp/achievements` | candidate |
| POST | `/api/candidates/me/fsp/sync` | candidate |
| PUT/DELETE | `/api/candidates/me/fsp/link` | candidate |
| GET | `/api/public/passports/{slug}` | публично |

---

## 5. Talent Pool и карточка

| Метод | Путь | Роль | Примечание |
| ----- | ---- | ---- | ---------- |
| GET | `/api/candidates` | employer/admin | фильтры, `vacancyId`, sort, page |
| GET | `/api/candidates/{id}` | employer/admin | без контактов |
| GET | `/api/candidates/{id}/contacts` | employer | после unlock |
| GET | `/api/candidates/{id}/fsp/achievements` | employer/admin | |
| GET | `/api/candidates/{id}/skill-radar` | user | кандидат — только свой |
| GET | `/api/vacancies/{id}/matches` | employer/admin | эквивалент pool по вакансии |

Query Talent Pool (основные): `vacancyId`, specialization/grade фильтры, `q`, `sort`, `page`, `limit` (≤50).

---

## 6. Employer / company / shortlist

| Метод | Путь | Роль |
| ----- | ---- | ---- |
| GET/POST | `/api/employer/vacancies` | employer/admin |
| GET | `/api/employer/offers` | employer |
| GET/POST/DELETE | `/api/employer/shortlist`… | employer |
| GET | `/api/employer/candidates/compare?ids=` | employer/admin |
| GET/PUT | `/api/employer/company` | employer |

---

## 7. Vacancies / applications

| Метод | Путь | Роль |
| ----- | ---- | ---- |
| GET | `/api/vacancies` | user |
| POST | `/api/vacancies/parse` | employer/admin |
| GET/PATCH | `/api/vacancies/{id}` | GET user / PATCH employer |
| GET | `/api/vacancies/{id}/match-to-me` | candidate |
| POST | `/api/vacancies/{id}/apply` | candidate |
| GET/POST/DELETE | `/api/candidate/saved-vacancies`… | candidate |

Зарплата вакансии и оффера — **RUB**; иная валюта → 422.

---

## 8. Offers

| Метод | Путь | Роль |
| ----- | ---- | ---- |
| POST | `/api/offers` | employer (email verified) |
| GET | `/api/offers/{id}` | участники / admin |
| POST | `/api/offers/{id}/accept` | candidate |
| POST | `/api/offers/{id}/decline` | candidate |
| POST | `/api/offers/{id}/withdraw` | employer |
| GET | `/api/candidate/offers` | candidate |

Правило контактов: после accept (или apply) `GET …/contacts` → 200; иначе `CONTACTS_LOCKED`.

---

## 9. Tests (assessment)

| Метод | Путь | Роль |
| ----- | ---- | ---- |
| POST | `/api/tests/sessions` | candidate |
| GET | `/api/tests/sessions/{id}/question` | candidate |
| POST | `/api/tests/sessions/{id}/answer` | candidate |
| POST | `/api/tests/sessions/{id}/finish` | candidate |
| GET | `/api/tests/sessions/{id}/result` | candidate |
| GET | `/api/tests/history` | candidate |

В вопросах до finish поле правильного ответа **не отдаётся**. Порог: `PASS_SCORE` (default 70).

---

## 10. Notifications / dashboards / admin

| Метод | Путь | Роль |
| ----- | ---- | ---- |
| GET/POST | `/api/notifications`… | user |
| GET | `/api/dashboard/candidate` | candidate |
| GET | `/api/dashboard/employer` | employer |
| GET | `/api/dashboard/employer/analytics` | employer |
| GET | `/api/admin/overview` | admin |
| GET | `/api/admin/users` | admin |
| POST | `/api/admin/users/{id}/status` | admin |
| GET | `/api/admin/offers` | admin |
| GET | `/api/admin/vacancies` | admin |
| GET | `/api/admin/assessments` | admin |
| GET | `/api/admin/categories` | admin |

---

## 11. ML-сервис (отдельный процесс, порт 8001)

Не под префиксом `/api` Backend. Вызывается только Backend'ом при `MATCHER_PROVIDER=ml`.

| Метод | Путь | Назначение |
| ----- | ---- | ---------- |
| GET | `/health` | health |
| POST | `/rank` | пакетный ranking (используется Backend) |
| POST | `/normalize-skills` | нормализация |
| POST | `/categorize` | мягкая категория |
| POST | `/grade-status` | статус грейда |
| POST | `/category-rank` | порядок в категории |

---

## 12. Согласованность с Frontend

Источник контракта для FE: `frontend/src/shared/api/endpoints.ts` + `entities/types.ts`.  
Интеграционный тест: `backend/tests/integration/test_frontend_contract.py`.

Изменение API: править schemas Backend и types Frontend **вместе**, обновить MSW handlers.
