# LCT Resonance — Frontend

Клиент **обратного рекрутинга**: кандидаты получают офферы, работодатели ищут в Talent Pool по Match Score и достижениям ФСП.

**Полный стек (FE + BE, интеграция, расхождения MSW ↔ API):** [`../README.md`](../README.md).  
Backend: [`../backend/README.md`](../backend/README.md) · Swagger при поднятом API: `http://localhost:8000/docs`.

Спеки:


| Документ                         | Зачем                                   |
| -------------------------------- | --------------------------------------- |
| `[TECH_SPEC.md](./TECH_SPEC.md)` | экраны, приоритеты P0–P2, контракт, DoD |
| `[UI_KIT.md](./UI_KIT.md)`       | токены, shared UI, domain-компоненты    |
| `/ui-kit`                        | живой каталог компонентов в рантайме    |


Frontend **не** считает Match Score, результаты теста, рейтинги и доступ к контактам — только UI + REST-клиент + RBAC-оболочки.

```
Frontend → Backend API → Matching/ML → Backend → Frontend
```

---



## Быстрый старт



### Демо без бэкенда (MSW)

```bash
cd frontend
npm install
VITE_USE_MOCKS=true npm run dev   # http://localhost:5173
```

С `VITE_USE_MOCKS=true` MSW поднимается при старте (`src/main.tsx` → `mocks/browser.ts`), Service Worker: `public/mockServiceWorker.js`.  
Пока моки включены, браузер **не** ходит на ваш API — отвечает SW.

### Демо-логины

Пароль для всех: `demo1234`


| Логин               | Роль      | Куда попадёте |
| ------------------- | --------- | ------------- |
| `candidate@demo.ru` | candidate | `/candidate`  |
| `employer@demo.ru`  | employer  | `/employer`   |
| `admin@demo.ru`     | admin     | `/admin`      |


Регистрация: `/register` (роли `candidate` | `employer`).

### С реальным бэкендом (по умолчанию)

1. Поднимите backend на `:8000` (см. `../backend/README.md`) и выполните сиды — демо-логины те же.
2. `npm run dev` без `VITE_USE_MOCKS`: Vite проксирует `/api` на `http://localhost:8000`
   (другой адрес — `VITE_API_PROXY_TARGET=http://host:port npm run dev`).
3. Backend реализует ровно контракт `src/entities/types.ts` + `src/shared/api/endpoints.ts`;
   ошибки приходят как `{ message, code, details, requestId }` — UI показывает `message`.

В Docker (`docker compose up` из корня) фронт собирается без моков, nginx проксирует `/api` на backend.

---



## Стек


| Слой         | Технология                               |
| ------------ | ---------------------------------------- |
| UI           | React 19, CSS Modules + global tokens    |
| Данные       | TanStack Query 5                         |
| Формы        | React Hook Form + Zod                    |
| Роутинг      | react-router-dom 7                       |
| HTTP         | `fetch` через единый `apiClient`         |
| Auth storage | memory + `sessionStorage` (`tokenStore`) |
| Моки         | MSW 2 (browser + Vitest server)          |
| Сборка       | Vite 6, TypeScript 5.8                   |
| Тесты        | Vitest + Testing Library + jsdom         |


Дизайн-токены и UI-kit: `[UI_KIT.md](./UI_KIT.md)`, живой гайд: `/ui-kit`.

---



## Архитектура `src/`

```
src/
├── app/                 # providers, router, layouts, guards
├── pages/               # route-level экраны
│   ├── auth/
│   ├── candidate/
│   ├── employer/
│   ├── admin/
│   ├── public/          # Career Passport, UI-kit
│   ├── shared/          # Notifications (обе роли)
│   └── landing/
├── features/            # auth context, notification bell
├── entities/            # типы DTO + domain UI (карточки, MatchScore, …)
├── mocks/               # MSW handlers + fixtures (+ reset для тестов)
├── styles/              # global.css (токены, shell)
└── shared/
    ├── api/             # client, endpoints, errors, token
    ├── config/          # env.ts
    ├── lib/             # formatters, labels
    └── ui/              # Button, Input, Modal, Loader, …
```

Алиас: `@/*` → `src/*` (`vite.config.ts` + `tsconfig`).

Правила слоёв:

- **pages** — fetch через TanStack Query + сборка экрана;
- **entities/ui** — презентация DTO, без прямых HTTP-вызовов;
- **shared/ui** — атомы без бизнес-правил;
- **mocks** — единственное место, где «считается» match/test для демо.

---



## Auth и роли



### Как работает

1. `POST /auth/login` или `/auth/register` → `{ accessToken, user }`.
2. Токен в `tokenStore` (memory + `sessionStorage`, ключ `lct_access_token`).
3. Каждый авторизованный запрос: `Authorization: Bearer <token>`, `Accept: application/json`.
4. `GET /auth/me` при старте, если токен есть.
5. `401` на запросе с auth → clear token + logout handler (редирект на логин через guards).
6. Logout: `POST /auth/logout` (best-effort) + clear queries.

Login/register `401` **не** сбрасывают сессию — показывают `message` с сервера.

### Guards


| Guard        | Поведение                               |
| ------------ | --------------------------------------- |
| `AuthGuard`  | нет токена/юзера → `/login`             |
| `GuestGuard` | уже залогинен → кабинет роли            |
| `RoleGuard`  | чужая роль → редирект в свой `roleHome` |


`roleHome`: `candidate` → `/candidate`, `employer` → `/employer`, `admin` → `/admin`.

### RBAC (UI)


| Роль        | Кабинет                                                           |
| ----------- | ----------------------------------------------------------------- |
| `candidate` | профиль, ФСП, офферы, тест, вакансии, уведомления                 |
| `employer`  | Talent Pool, вакансии CRUD, shortlist, compare, офферы, analytics |
| `admin`     | overview, users (block), offers, vacancies                        |


Контакты кандидата работодателю: только `GET /candidates/:id/contacts` после Accept на бэке (`403` → UI «скрыты»). Фронт **не** раскрывает контакты по статусу оффера в обход API.

---



## HTTP-контракт (что UI реально дергает)

База: `{apiBaseUrl}` (дефолт `/api`). Клиент: `src/shared/api/endpoints.ts`.  
Типы: `src/entities/types.ts`. Референс поведения: `src/mocks/handlers.ts` + `fixtures.ts`.

### Ошибки

```json
{ "message": "human readable" }
```

UI читает `message`. Статусы, на которые завязаны сценарии: `400`, `401`, `403`, `404`.

### Auth


| Method | Path             | Auth | Назначение           |
| ------ | ---------------- | ---- | -------------------- |
| POST   | `/auth/login`    | no   | логин                |
| POST   | `/auth/register` | no   | регистрация          |
| POST   | `/auth/logout`   | yes  | логаут               |
| GET    | `/auth/me`       | yes  | текущий пользователь |




### Candidate / profile / FSP


| Method    | Path                                | Назначение              |
| --------- | ----------------------------------- | ----------------------- |
| GET/PATCH | `/candidates/me`                    | свой профиль            |
| GET       | `/candidates/me/completeness`       | checklist заполненности |
| GET       | `/candidates/me/fsp/achievements`   | достижения              |
| POST      | `/candidates/me/fsp/sync`           | синхронизация ФСП       |
| GET       | `/candidates/:id`                   | профиль (employer view) |
| GET       | `/candidates/:id/fsp/achievements`  | FSP чужого кандидата    |
| GET       | `/candidates/:id/contacts`          | контакты после Accept   |
| GET       | `/candidates/:id/skill-radar`       | оси Skill Radar (0…100) |
| GET       | `/candidates`                       | Talent Pool + фильтры   |
| GET       | `/employer/candidates/compare?ids=` | сравнение ≥2            |




#### Query Talent Pool

`specialization`, `grade`, `skills`, `workFormat`, `salaryFrom`, `salaryTo`, `fspDiscipline`, `hasFspAchievements`, `readiness`, `vacancyId`, `q`, `page`, `limit`, `sort` (`match`  `grade`  `salary`  `name`).

При `vacancyId` в items приходит `match` (score + reasons + missing skills). Сортировка/score — **только Backend**.

### Vacancies


| Method          | Path                               | Назначение                                                     |
| --------------- | ---------------------------------- | -------------------------------------------------------------- |
| GET/POST        | `/employer/vacancies`              | список / создание                                              |
| GET/PATCH       | `/vacancies/:id`                   | просмотр / правка                                              |
| GET             | `/vacancies`                       | каталог кандидата (`matchToMe`, `savedOnly`, `specialization`) |
| GET             | `/vacancies/:id/match-to-me`       | Match для текущего кандидата                                   |
| POST            | `/vacancies/:id/apply`             | отклик                                                         |
| POST            | `/vacancies/parse`                 | AI-черновик вакансии (текст → поля)                            |
| GET/POST/DELETE | `/candidate/saved-vacancies[/:id]` | избранное                                                      |




### Offers / shortlist


| Method          | Path                                 | Назначение                                |
| --------------- | ------------------------------------ | ----------------------------------------- |
| POST            | `/offers`                            | создать оффер (зарплата обязательна в UI) |
| GET             | `/candidate/offers`                  | inbox                                     |
| GET             | `/employer/offers`                   | исходящие                                 |
| GET             | `/offers/:id`                        | детали (может перевести `new` → `viewed`) |
| POST            | `/offers/:id/accept` | `/decline`    | ответ кандидата                           |
| GET/POST/DELETE | `/employer/shortlist[/:candidateId]` | shortlist                                 |




### Testing


| Method | Path                           | Назначение                       |
| ------ | ------------------------------ | -------------------------------- |
| POST   | `/tests/sessions`              | старт (`retest?`)                |
| GET    | `/tests/sessions/:id/question` | вопрос **без** `correctOptionId` |
| POST   | `/tests/sessions/:id/answer`   | ответ                            |
| POST   | `/tests/sessions/:id/finish`   | результат                        |
| GET    | `/tests/sessions/:id/result`   | результат                        |
| GET    | `/tests/history`               | история / retest                 |




### Dashboard / analytics / notifications / admin / public


| Method | Path                                 | Назначение                     |
| ------ | ------------------------------------ | ------------------------------ |
| GET    | `/dashboard/candidate`               | сводка + completeness/unread   |
| GET    | `/dashboard/employer`                | сводка                         |
| GET    | `/dashboard/employer/analytics`      | funnel, conversion, top skills |
| GET    | `/notifications`                     | список + `unread`              |
| POST   | `/notifications/:id/read`            | прочитать                      |
| POST   | `/notifications/read-all`            | всё прочитано                  |
| GET    | `/admin/overview`                    | метрики                        |
| GET    | `/admin/users`                       | пользователи                   |
| POST   | `/admin/users/:id/status`            | `active` | `blocked`           |
| GET    | `/admin/offers` | `/admin/vacancies` | модерация-списки               |
| GET    | `/candidates/me/passport`            | своя ссылка на паспорт         |
| GET    | `/public/passports/:slug`            | Career Passport (без auth)     |


---



## Страницы ↔ API



### Публичные


| Route                 | Основные вызовы                                                    |
| --------------------- | ------------------------------------------------------------------ |
| `/`                   | лендинг; редирект в кабинет если уже auth                          |
| `/login`, `/register` | auth                                                               |
| `/ui-kit`             | —                                                                  |
| `/p/:slug`            | `GET /public/passports/:slug` (QR + radar + профиль без контактов) |




### Candidate


| Route                           | Основные вызовы                              |
| ------------------------------- | -------------------------------------------- |
| `/candidate`                    | dashboard + completeness                     |
| `/candidate/profile` | `/edit`  | me, fsp, skill-radar, PATCH                  |
| `/candidate/fsp`                | achievements + sync                          |
| `/candidate/offers` | `/:id`    | list / detail / accept / decline             |
| `/candidate/testing`…           | sessions, question, answer, finish, history  |
| `/candidate/vacancies` | `/:id` | list (+ matchToMe), match-to-me, apply, save |
| `/candidate/notifications`      | notifications CRUD-read                      |




### Employer


| Route                      | Основные вызовы                                 |
| -------------------------- | ----------------------------------------------- |
| `/employer`                | dashboard + analytics                           |
| `/employer/talent-pool`    | candidates + vacancies (для Match)              |
| `/employer/candidates/:id` | profile, fsp, radar, contacts, shortlist, offer |
| `/employer/vacancies`…     | CRUD + AI parse                                 |
| `/employer/shortlist`      | shortlist                                       |
| `/employer/compare?ids=`   | compare + radars + skill matrix                 |
| `/employer/offers`         | исходящие                                       |
| `/employer/notifications`  | notifications                                   |




### Admin


| Route                               | Основные вызовы |
| ----------------------------------- | --------------- |
| `/admin`                            | overview        |
| `/admin/users`                      | users + block   |
| `/admin/offers`, `/admin/vacancies` | списки          |


---



## Ключевые продуктовые правила (не ломать)

1. **Match Score / Skill Radar / test score / AI parse** — только ответы API, без формул на клиенте.
2. Self-reported skills **не** помечать FSP Verified.
3. Correct answers теста не приходят до `finish`.
4. Контакты — только успешный GET contacts.
5. Optimistic UI на accept/decline допустим с откатом при ошибке.
6. Talent Pool: фильтры → query → Backend (debounce ~300ms на текст); не фильтровать полный датасет на клиенте как основной режим.

Happy path (DoD P0 на моках):  
employer создаёт вакансию → Talent Pool + Match → оффер с зарплатой → candidate accept → employer получает contacts.

---



## UI-состояния

Каждый data-view: loading / success / empty / error / disabled / action success.  
Shared: `Loader`, `EmptyState`, `ErrorState` (`shared/ui`).

Domain-компоненты (см. UI_KIT):  
`CandidateCard`, `CandidateProfile`, `MatchScore`, `MatchReason`, `OfferCard`, `OfferForm`, `VacancyCard`, `SkillRadar`, `FSPAchievementCard`, `FSPVerificationBadge`, `TestQuestion`, `TestResult`, `ProfileCompleteness`, …

---



## Тестирование

```bash
npm run test          # vitest run
npm run test:watch    # watch
```

- Setup: `src/test/setup.ts` — MSW server + `resetMockDb` / `resetTestSessions` на каждый тест.
- Helpers: `src/test/test-utils.tsx` (`renderWithProviders`).
- Контрактные: `shared/api/p0.dod.test.ts`, `p2.features.test.ts`, `p3.features.test.ts`, `analytics.retest.test.ts`, `client.auth.test.ts`.
- Flow/UI: pages + entities `*.test.tsx`.

E2E отдельным раннером пока нет — сценарии закрываются Vitest + MSW.

---



## Скрипты


| Команда              | Что делает              |
| -------------------- | ----------------------- |
| `npm run dev`        | Vite `:5173`            |
| `npm run build`      | `tsc -b` + `vite build` |
| `npm run preview`    | превью `dist`           |
| `npm run lint`       | ESLint                  |
| `npm run test`       | Vitest once             |
| `npm run test:watch` | Vitest watch            |


