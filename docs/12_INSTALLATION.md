# 12. Установка и запуск с нуля

Инструкция для проверяющего на чистой машине. Команды проверены по `compose.yaml`, `SETUP.md`, README.  
Если шаг не гонялся в среде подготовки документации — помечено **Не проверено в текущем окружении**.

Дублирующая подробная шпаргалка команды: корневой файл `SETUP.md`.

---

## 1. Системные требования

| Компонент | Требование |
| --------- | ---------- |
| ОС | macOS, Linux, Windows 10/11 с Docker Desktop или WSL2 |
| Docker | Docker Engine + Compose v2 (Desktop / OrbStack) |
| Python (локальный BE/ML) | 3.12+ |
| Node.js (локальный FE) | 20+ (в Docker-сборке FE используется Node 22) |
| PostgreSQL | 16 (из compose или свой) |
| uv | для локального Backend/ML |
| ОЗУ | рекомендация ≥ 8 ГБ для полного compose (не бенчмаркировано) |
| Диск | рекомендация ≥ 5 ГБ под образы |
| Порты хоста | 8080 (UI), 8000 (API), 8001 (ML), 8025/1025 (Mailpit), 5432 (Postgres), 5173 (Vite dev) |

---

## 2. Docker-развёртывание (рекомендуется жюри)

### Шаг 1. Установить Docker

Установите Docker Desktop (Windows/macOS) или Docker Engine + Compose (Linux). Убедитесь, что команда `docker compose version` выполняется.

### Шаг 2. Получить код

```bash
git clone <URL_РЕПОЗИТОРИЯ_КОМАНДЫ>
cd LCT_Resonance
```

URL репозитория подставьте актуальный (в старых заметках встречался `ResonanceTECH/LCT_Resonance` — проверьте у команды).

### Шаг 3. Корневой `.env`

Создайте файл `.env` в корне:

```env
POSTGRES_PASSWORD=DemoPass123
```

Только латиница и цифры: пароль подставляется в URL без экранирования спецсимволов.

### Шаг 4. `backend/.env`

```bash
cp backend/.env.example backend/.env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Вставьте вывод в `JWT_SECRET=` (не короче 32 символов). Остальное для Docker перекрывает `compose.yaml`.

### Шаг 5–6. Сборка и запуск

```bash
docker compose up -d --build
```

Первая сборка занимает несколько минут. Миграции и seed выполняются при старте backend (`SEED_ON_START=true`).

Опционально ranking через ML-контейнер:

```bash
MATCHER_PROVIDER=ml docker compose up -d --build
```

### Шаг 7–11. Проверка

| Что открыть в браузере | Ожидание |
| ---------------------- | -------- |
| http://localhost:8080 | лендинг FSP Talent |
| http://localhost:8080/api/docs | Swagger |
| http://localhost:8025 | Mailpit UI |
| http://localhost:8001/health | JSON status ML |

```bash
docker compose ps
curl -s http://localhost:8000/api/health/ready
```

### Шаг 12–15. Операции

```bash
docker compose logs -f backend
docker compose restart backend
docker compose up -d --build backend
docker compose down          # данные PG сохраняются
docker compose down -v       # УДАЛИТ БД — чистый seed при следующем up
```

Обновление кода: `git pull`, затем `docker compose up -d --build`.

---

## 3. Локальный запуск без полного Docker

### 3.1. PostgreSQL + Mailpit из compose

```bash
# корневой .env с POSTGRES_PASSWORD уже есть
docker compose up -d postgres mailpit
```

### 3.2. Backend

```bash
cd backend
cp .env.example .env
# заполнить DATABASE_URL*, JWT_SECRET, APP_ENV=dev
uv sync
uv run alembic upgrade head
uv run python -m app.seed
uv run uvicorn app.main:app --reload --port 8000
```

Проверка: http://localhost:8000/api/docs

### 3.3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Открыть: http://localhost:5173  
Прокси `/api` → http://localhost:8000

Моки без Backend:

```bash
VITE_USE_MOCKS=true npm run dev
```

Windows PowerShell:

```powershell
$env:VITE_USE_MOCKS="true"; npm run dev
```

### 3.4. ML (опционально)

```bash
cd ml
uv sync --group dev
uv run uvicorn app.main:app --reload --port 8001
```

В `backend/.env`: `MATCHER_PROVIDER=ml`, `ML_MATCHER_URL=http://localhost:8001`.

---

## 4. Особенности localhost и Docker-сети

| Откуда | Как писать адрес Postgres | Как писать ML |
| ------ | ------------------------- | ------------- |
| Backend в контейнере | хост `postgres`, пользователь/пароль/БД из env | `http://ml:8001` |
| Backend на хосте | `localhost:5432` | `http://localhost:8001` |
| Браузер | UI `localhost:8080` или `:5173` | не вызывает ML |

`DATABASE_URL` в compose задаётся явно и **перекрывает** `backend/.env`.

CORS: при одном origin через nginx (8080) отдельный CORS для UI не критичен. Для Vite `:5173` в `.env` указано `CORS_ORIGINS=http://localhost:5173`.

---

## 5. Чек-лист после установки

- [ ] `GET /api/health/ready` → status ok  
- [ ] Swagger открывается  
- [ ] UI открывается  
- [ ] Логин `employer@demo.ru` / `demo1234` успешен  
- [ ] Talent Pool по вакансии показывает score  
- [ ] Mailpit ловит письма при новой регистрации (compose)  
- [ ] `VITE_USE_MOCKS` в Docker = false (сеть доходит до Backend)

---

## 6. Повторяемость

Все шаги опираются на файлы репозитория и seed. Не требуются ручные правки БД на машине разработчика.  
Повторная установка: `down -v` → `up --build` или локально пересоздать БД + `alembic upgrade` + `python -m app.seed`.
