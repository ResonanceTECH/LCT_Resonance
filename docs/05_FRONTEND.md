# 05. Frontend

Стек (из `frontend/package.json`): React ^19.1, React DOM ^19.1, TypeScript ~5.8.3, Vite ^6.3.3, React Router DOM ^7.5.1, TanStack Query ^5.74.4, React Hook Form ^7.56, Zod ^3.24.3, MSW ^2.7.5, Vitest ^5.0.3, Testing Library.

Порт dev: **5173**. Docker: nginx на **8080**.

---

## 1. Структура `frontend/src`

```text
src/
├── app/           router.tsx, guards.tsx, layouts.tsx, providers.tsx
├── pages/         landing, auth, candidate, employer, admin, public, shared
├── entities/      types.ts (контракт), domain UI
├── features/      auth, notifications
├── mocks/         handlers.ts, fixtures.ts, browser.ts, server.ts
├── shared/        api/, config/, ui/, lib/
└── styles/
```

---

## 2. Маршрутизация

Роутер: `src/app/router.tsx`. Guards: GuestGuard, AuthGuard, RoleGuard.

| Префикс | Роль | Примеры экранов |
| ------- | ---- | --------------- |
| `/` | публичный | лендинг |
| `/login`, `/register` | гость | вход / регистрация |
| `/p/:slug` | публичный | Career Passport |
| `/candidate/*` | candidate | dashboard, profile, testing, offers, vacancies, fsp |
| `/employer/*` | employer | dashboard, talent-pool, vacancies, offers, shortlist, compare |
| `/admin/*` | admin | overview, users, assessments, categories, offers, vacancies |

Полная таблица маршрутов — в аудите кода; ключевые пути для пользователя перечислены в `14_USER_GUIDE_CANDIDATE.md` и `15_USER_GUIDE_EMPLOYER.md`.

---

## 3. Работа с API

- Base URL: `VITE_API_BASE_URL` или `/api` (`src/shared/config/env.ts`).
- Клиент: `src/shared/api/client.ts` — fetch + Bearer из `sessionStorage` (`lct_access_token`).
- Пути: `src/shared/api/endpoints.ts`.
- Типы DTO: `src/entities/types.ts` (camelCase).
- Состояние сервера: TanStack Query.
- Формы: React Hook Form + Zod resolvers.
- Ошибки: плоский `{ message, code, details, requestId }` — показ `message`.

Анти-цели UI (из README): не считать match/test на клиенте; не ходить в ФСП напрямую; не раскрывать контакты в обход API.

---

## 4. Реальные данные и mock-режим

| Переменная | Значение | Эффект |
| ---------- | -------- | ------ |
| `VITE_USE_MOCKS` | не задана / не `true` | запросы идут на Backend (через Vite proxy или nginx) |
| `VITE_USE_MOCKS=true` | строка `'true'` | в `main.tsx` стартует MSW Service Worker |

Docker compose: build-arg `${VITE_USE_MOCKS:-false}` → **по умолчанию реальный FastAPI**.

Vite proxy: `/api` → `VITE_API_PROXY_TARGET` или `http://localhost:8000`.

MSW handlers: `src/mocks/handlers.ts`. Демо-аккаунты совпадают с backend seed (`demo1234`).

Vitest всегда поднимает MSW node (`src/test/setup.ts`), независимо от env.

**Вывод:** интеграция Frontend↔Backend для Docker-стенда завершена при `VITE_USE_MOCKS=false`. Режим моков — для UI-демо без Backend и для unit-тестов.

---

## 5. RBAC в UI

После login редирект: `roleHome` → `/candidate` | `/employer` | `/admin`.  
Чужая роль → редирект в свой кабинет.  
Admin через `/register` создать нельзя — только seed/Backend.

Баннер неподтверждённого email в layout: resend verification.

---

## 6. Дизайн-система

Токены и компоненты: `frontend/UI_KIT.md`, живой каталог маршрут `/ui-kit`.  
Брендовые цвета ФСП используются в UI (фиолетовый `#402FFF` и др. — см. UI_KIT).

---

## 7. Тесты Frontend

```bash
cd frontend
npm run test
npm run lint
npm run build
```

Покрытие: DoD golden path на MSW, auth, admin RBAC, employer/candidate flows, entities. Отдельного E2E (Playwright/Cypress) в репозитории нет.
