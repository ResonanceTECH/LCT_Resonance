# 21. Технологии и лицензии

Версии — из манифестов проекта (`package.json`, `pyproject.toml`, образы compose).  
Лицензия репозитория: см. корневой `LICENSE` (файл присутствует). Лицензии транзитивных npm/PyPI пакетов здесь **не угадываются** — смотрите lock-файлы и сайты пакетов.

---

## Frontend

| Компонент | Технология | Версия (declared) | Назначение |
| --------- | ---------- | ----------------- | ---------- |
| UI | React / React DOM | ^19.1.0 | SPA |
| Язык | TypeScript | ~5.8.3 | типизация |
| Сборка | Vite | ^6.3.3 | bundler |
| Роутинг | react-router-dom | ^7.5.1 | routes |
| Данные | @tanstack/react-query | ^5.74.4 | server state |
| Формы | react-hook-form + zod | ^7.56 / ^3.24 | валидация |
| Моки | msw | ^2.7.5 | demo/tests |
| Тесты | vitest + Testing Library | ^5.0 / ^16.3 | unit |
| Иконки | lucide-react, hugeicons | см. package.json | UI |
| QR | qrcode.react | ^4.2.0 | passport |
| Prod image | nginx | 1.27-alpine | static+proxy |
| Build image | node | 22-alpine | CI build |

---

## Backend

| Компонент | Технология | Версия | Назначение |
| --------- | ---------- | ------ | ---------- |
| Runtime | Python | ≥3.12 | |
| HTTP | FastAPI | ≥0.143 | API |
| Server | Uvicorn | ≥0.54 | ASGI |
| ORM | SQLAlchemy asyncio | ≥2.1.4 | models |
| Migrations | Alembic | ≥1.20 | schema |
| Validation | Pydantic Settings | ≥2.15 | config |
| DB drivers | asyncpg, psycopg | ≥0.32 / ≥3.3 | Postgres |
| Auth | PyJWT, argon2-cffi | ≥2.15 / ≥25.1 | JWT/пароли |
| HTTP client | httpx | ≥0.28 | ML/FSP |
| Tests | pytest, pytest-asyncio | ≥9.1 / ≥1.4 | |

---

## ML

| Компонент | Технология | Версия | Назначение |
| --------- | ---------- | ------ | ---------- |
| HTTP | FastAPI | ≥0.143 | /rank и др. |
| Schemas | Pydantic | ≥2.10 | DTO |
| Server | Uvicorn | ≥0.54 | |
| ML libs (torch и т.п.) | — | — | **не используются** |

---

## Database / Infra

| Компонент | Технология | Версия | Назначение |
| --------- | ---------- | ------ | ---------- |
| БД | PostgreSQL | 16-alpine | данные |
| Orchestration | Docker Compose | compose.yaml | стенд |
| Mail catcher | Mailpit | latest | демо-почта |
| Cloud (заготовка) | Render + Neon + Vercel | render.yaml, vercel.json | деплой |

---

## Инструменты разработки

| Инструмент | Назначение |
| ---------- | ---------- |
| uv | зависимости Python |
| npm | зависимости Frontend |
| ESLint | lint FE |
