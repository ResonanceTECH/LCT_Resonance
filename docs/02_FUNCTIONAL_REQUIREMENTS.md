# 02. Функциональные требования и статус реализации

Матрица построена по коду Frontend, Backend и ML. Статусы:

- **РП** — реализовано и проверено автотестами или compose-сценарием
- **РН** — реализовано, автотестом не покрыто / не проверено в текущем окружении документации
- **МС** — работает на MSW (Frontend), Backend-эквивалент есть или частично
- **ЧР** — частично
- **НР** — не реализовано
- **ПЛ** — запланировано после MVP

Официальный PDF ТЗ не найден; колонка «Требование ТЗ» опирается на формулировки из `Backend.md` / внутренних спецификаций.

---

## 1. Кандидат

| ID | Функция | Требование ТЗ (внутр.) | Реализация | Статус | Где проверить |
| -- | ------- | --------------------- | ---------- | ------ | ------------- |
| C01 | Регистрация с ролью candidate | Обязательный путь | `POST /api/auth/register`, UI `/register` | РП | LoginPage.test, golden path |
| C02 | Подтверждение email | Обязательно | письмо + Mailpit / лог; `verify-email` | РП | SETUP.md, Mailpit :8025 |
| C03 | Авторизация | Да | JWT access 8ч, UI login | РП | auth tests |
| C04 | Опрос отрасль/специализация | Путь к категории | специализация в профиле + старт теста; отдельного «опроса отрасль» нет | ЧР | `/candidate/profile/edit`, `/candidate/testing` |
| C05 | Выбор предполагаемого грейда | Да | `declared` grade в профиле / сессии теста | РП | testing API |
| C06 | Тестирование 10 вопросов | Да | `/api/tests/sessions`… | РП | test_testing_logic, UI TestingPage |
| C07 | Подтверждённая категория | Да | verified spec+grade при score≥70 | РП | finish session |
| C08 | История тестирования | Да | `GET /api/tests/history` | РП | UI result/history |
| C09 | Пересдача / cooldown | Ограничение частоты | 24ч retry same/higher; 90д смена категории | РП | testing service |
| C10 | Редактирование профиля | Да | PATCH `/candidates/me` | РП | Profile edit |
| C11 | Заполнение резюме / about | Да | поля профиля | РП | profile |
| C12 | Импорт PDF резюме | — | нет | НР | — |
| C13 | Экспорт PDF паспорта | Желательно | публичный паспорт + QR; отдельной генерации PDF-файла на Backend нет | ЧР | `/p/:slug`, passport API |
| C14 | Связь с FSP ID | Да (mock OK) | link/sync, mock fixtures | РП | FSP page, test_fsp_mock |
| C15 | Достижения ФСП | Да | achievements list | РП | `/candidate/fsp` |
| C16 | Приватность / видимость | Да | profileVisibility, contactsVisibility | РП | profile + pool gate |
| C17 | Согласия | Да | consents API | РП | registration + settings |
| C18 | Получение приглашений | Да | `/candidate/offers` | РП | Offers UI |
| C19 | Accept / Decline | Да | POST accept/decline | РП | OfferDetail test |
| C20 | Вакансии и отклики | Доп. сценарий | каталог, apply, saved | РП | Vacancies UI, p3 tests |

---

## 2. Работодатель

| ID | Функция | Требование | Реализация | Статус | Где проверить |
| -- | ------- | ---------- | ---------- | ------ | ------------- |
| E01 | Регистрация employer | Да | register role=employer | РП | register |
| E02 | Профиль компании | Да | GET/PUT `/employer/company` | РП | создаётся из companyName при вакансии |
| E03 | Описание потребности | Да | вакансия (в т.ч. draft) | РП | `/employer/vacancies/new` |
| E04 | Каталог категорий | Да | specializations + grades | РП | taxonomy API |
| E05 | Talent Pool | Да | `GET /candidates?vacancyId=` | РП | `/employer/talent-pool` |
| E06 | Поиск и фильтры | Да | query params, debounce UI | РП | TalentPoolPage |
| E07 | Matching score | Да | baseline / ML `/rank` | РП | pool + matching tests |
| E08 | Объяснения | Да | reason codes + labels | РП | candidate detail |
| E09 | Shortlist | Доп. | shortlist API + UI | РП | `/employer/shortlist` |
| E10 | Сохранение поискового контекста | — | фильтры в URL; отдельной search-session таблицы нет | ЧР | query string pool |
| E11 | Карточка кандидата | Да | `/employer/candidates/:id` | РП | detail page |
| E12 | Отправка оффера | Да | `POST /offers` + salary RUB | РП | OfferForm |
| E13 | Зарплатная вилка | Да | обязательна в рублях | РП | schemas |
| E14 | Статусы офферов | Да | pending/viewed/accepted/… | РП | offers list |
| E15 | Контакты после согласия | Да | `GET …/contacts`, иначе 403 | РП | golden path |
| E16 | Публикация вакансий | Доп. | status active/draft/closed | РП | vacancies |
| E17 | Compare | Доп. | 2–4 кандидатов | РП | `/employer/compare` |
| E18 | Parse текста вакансии | Доп. | `POST /vacancies/parse` | РП | VacancyForm |
| E19 | Аналитика работодателя | Доп. | dashboard analytics | РП | employer dashboard |

---

## 3. Администратор

| ID | Функция | Реализация | Статус | Примечание |
| -- | ------- | ---------- | ------ | ---------- |
| A01 | Dashboard overview | `/admin/overview` | РП | доп. модуль |
| A02 | Users + block/unblock | status API | РП | |
| A03 | Assessments view | read-only UI | ЧР | каталог/попытки |
| A04 | Categories view | read-only | ЧР | «правка позже» в UI |
| A05 | Offers / Vacancies lists | read | РП | |
| A06 | Audit log UI | таблица `audit_events` есть, отдельного экрана нет | ЧР | события пишутся в БД |

---

## 4. Системные / сквозные

| ID | Функция | Статус | Комментарий |
| -- | ------- | ------ | ----------- |
| S01 | Docker compose стенд | РП | UI :8080, API, PG, Mailpit, ML |
| S02 | OpenAPI / Swagger | РП | `/api/docs` |
| S03 | FE↔BE контрактный тест | РП | test_frontend_contract |
| S04 | MSW offline demo | РП | `VITE_USE_MOCKS=true` |
| S05 | Keycloak / OIDC | ПЛ | в коде JWT; адаптер AuthProvider не внедрён |
| S06 | Реальное API ФСП | НР | MockFSPAdapter + stub RealFSPAdapter |
| S07 | PDF resume import | НР | |
| S08 | Embeddings matching | НР | осознанно |

---

## 5. Frontend ↔ Backend vs MSW

| Режим | Как включить | Данные |
| ----- | ------------ | ------ |
| Docker жюри (по умолчанию) | `docker compose up` , `VITE_USE_MOCKS=false` | Реальный FastAPI + Postgres |
| Локальная разработка | `npm run dev` + backend :8000 | Vite proxy `/api` → FastAPI |
| Только UI на моках | `VITE_USE_MOCKS=true npm run dev` | MSW, Backend не нужен |
| Vitest | всегда | MSW node server |

**Нельзя** называть интеграцию «только моки», если стенд поднят через compose с `VITE_USE_MOCKS=false` (значение по умолчанию в `compose.yaml`).

---

## 6. Продуктовые сущности в реализации

| Понятие | Как хранится |
| ------- | ------------ |
| Пользователь | `users` |
| Кандидат | `candidate_profiles` (PK = user_id) |
| Работодатель | `users.role=employer` + `companies.owner_user_id` |
| Компания | `companies` |
| Специализация / грейд / навык | `specializations`, `grades`, `skills` |
| Категория | пара verified_specialization + verified_grade |
| Карьерный паспорт | поля профиля + `passport_token` + public endpoint |
| Тест / попытка | `test_attempts`, `test_attempt_items`, `test_questions` |
| Достижение ФСП | `fsp_achievements`, `fsp_links` |
| Потребность | `vacancies` (+ skills) |
| Подборка | ответ Talent Pool (не отдельная таблица) |
| Match Score | вычисляется matcher'ом, не персистится как история |
| Приглашение | `offers` |
| Отклик | `applications` |
| Согласие | `consents` |
| Shortlist | `shortlist_items` |
| Уведомление | `notifications` |
