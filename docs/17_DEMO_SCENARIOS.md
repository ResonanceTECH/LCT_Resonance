# 17. Демонстрационные сценарии для жюри

## Как проверить FSP Talent за 5–10 минут

### Быстрый доступ

| Ресурс | Адрес / значение |
| ------ | ---------------- |
| Приложение (Docker) | http://localhost:8080 |
| Swagger | http://localhost:8080/api/docs |
| Mailpit | http://localhost:8025 |
| ML health | http://localhost:8001/health |
| Публичный стенд | Не указан / требуется добавить командой после деплоя |
| Видео / презентация | Не указаны в репозитории как проверенные URL |
| Пароль всех демо | `demo1234` |

Демо-аккаунты:

| Роль | Email |
| ---- | ----- |
| employer | `employer@demo.ru` |
| candidate | `candidate@demo.ru` |
| candidate без упора на ФСП | например `elena@demo.ru` / filler без FSP |
| admin | `admin@demo.ru` |

Запуск стенда: `docker compose up -d --build` (см. `12_INSTALLATION.md`).

Как убедиться, что данные с Backend, а не MSW: в DevTools Network запросы `/api/*` идут на тот же origin `:8080` и возвращают заголовки/тела FastAPI; в compose `VITE_USE_MOCKS=false`.

---

## Сценарий A — кандидат (подтверждение категории)

1. Выйти из системы, если залогинены.
2. Войти: `candidate@demo.ru` / `demo1234`.
3. Открыть `/candidate/profile` — Frontend Middle, тест ~82, ФСП.
4. Открыть `/candidate/testing` — история / возможность пересдачи с ограничениями.
5. Открыть `/candidate/fsp` — достижения mock.

Для полного пути «с нуля»: зарегистрировать нового кандидата → Mailpit confirm → заполнить профиль → пройти тест → увидеть verified.

Ожидание: подтверждённая категория в профиле; кандидат в пуле соответствующих вакансий.

---

## Сценарий B — работодатель (Talent Pool → оффер)

1. Войти: `employer@demo.ru` / `demo1234`.
2. `/employer/vacancies` — открыть демо-вакансию Frontend Middle (или создать новую).
3. `/employer/talent-pool` — выбрать эту вакансию.
4. Убедиться: у кандидатов есть score и причины; Анна ранжируется конкурентоспособно относительно слабого стека.
5. Открыть карточку кандидата → отправить оффер с зарплатой в рублях.

Ожидание: оффер создан; у кандидата появится во входящих.

---

## Сценарий C — взаимодействие Accept → контакты

1. Под employer отправить оффер кандидату `candidate@demo.ru` (если ещё нет активного).
2. Logout → login как candidate.
3. `/candidate/offers` → открыть → **Принять**.
4. Logout → login employer.
5. Карточка кандидата → контакты отображаются (API 200).

Ожидание: до Accept контакты недоступны; после — доступны.

---

## Сценарий D — приватность

1. Employer открывает кандидата **без** accepted offer и **без** application.
2. Запрос контактов → отказ / сообщение о блокировке (`CONTACTS_LOCKED`).
3. После Accept того же employer — контакты видны.
4. Другой employer (`employer2@demo.ru`) без своего Accept — контакты по-прежнему закрыты.

---

## Сценарий E — тестирование

1. Новый кандидат или аккаунт без cooldown.
2. Старт двух сессий (два пользователя) на одну категорию — сравнить, что вопросы/seed различаются.
3. Finish с разным качеством ответов → pass/fail.
4. Проверить, что correct не приходит в JSON вопроса (Network).

---

## Сценарий F — matching

1. Employer: вакансия Frontend Middle с required React/TypeScript.
2. Pool: порядок и reasons.
3. Изменить навыки/зарплату вакансии (edit) → обновить pool — подборка пересчитывается (score не кешируется в БД как история).

Эталонные числа демо-batch ML — в `08_ML_MATCHING.md`.

---

## Сценарий G — без достижений ФСП

1. Найти в pool / профилях кандидата без FSP (например сценарии seed `no-fsp` логика / elena).
2. Убедиться: кандидат в пуле при confirmed категории; вклад fsp = 0; нет ошибки sync обязательности.

---

## Сценарий H — дополнительные функции

| Функция | Куда |
| ------- | ---- |
| Shortlist | `/employer/shortlist` |
| Compare | `/employer/compare?ids=` |
| Вакансии кандидата + apply | `/candidate/vacancies` |
| Admin | `admin@demo.ru` → `/admin/overview`, block user |
| Career Passport | публикация в профиле → `/p/...` |
| UI Kit | `/ui-kit` |

---

## Если операция недоступна

| Симптом | Действие |
| ------- | -------- |
| Не логинится demo | seed не применён: `docker compose logs backend`, `SEED_ON_START` |
| Пустой Talent Pool | нет кандидатов с verified категорией вакансии; взять seed Frontend Middle |
| Не уходит оффер | email работодателя не verified |
| Нет писем | Mailpit не поднят; или APP_ENV/SMTP |
| UI «как будто моки» | проверить что сборка без `VITE_USE_MOCKS=true` |
