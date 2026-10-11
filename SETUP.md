# Запуск LCT Resonance

Пошаговая инструкция для команды: от чистой машины до работающего стенда с демо-данными.
Обзор продукта и контракт API — в [README.md](./README.md), устройство бэкенда — в
[backend/README.md](./backend/README.md).

|              | Docker                                       | Локально                                                  |
| ------------ | -------------------------------------------- | --------------------------------------------------------- |
| Когда        | показать стенд, проверить «как у жюри»       | разработка: перезагрузка при правках, отладчик            |
| Нужно        | Docker Desktop                               | Python 3.12+, uv, Node.js 20+, PostgreSQL 16 (или Docker) |
| Адрес        | http://localhost:8080                        | http://localhost:5173                                     |
| Письма       | Mailpit: http://localhost:8025               | ссылка в логе бэкенда или Mailpit, см. [Почта](#почта)    |

---

## Получить код

```bash
git clone git@github.com:ResonanceTECH/LCT_Resonance.git
cd LCT_Resonance
git checkout backend_dev   # пока бэкенд не влит в main
```

---

## Вариант 1. Docker

1. Запустите Docker Desktop.
2. Создайте файл `.env` в корне репозитория:

   ```env
   POSTGRES_PASSWORD=придумайте_пароль
   ADMIN_EMAIL=admin@ваш-домен.ru
   ADMIN_PASSWORD=пароль_администратора_от_8_символов
   # SEED_DEMO=true        # только для демо-стенда: добавит демо-аккаунты
   ```

   Пароль базы — только латиница и цифры: он подставляется в строку подключения как есть,
   и символы вроде `!`, `@`, `:` её ломают. Администратор создаётся при первом старте; без
   `ADMIN_EMAIL` в админку войти будет некем.
3. Создайте `backend/.env` из шаблона и заполните в нём `JWT_SECRET`:

   ```bash
   cp backend/.env.example backend/.env    # PowerShell: Copy-Item backend/.env.example backend/.env
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Вставьте напечатанную строку после `JWT_SECRET=`. Остальное в `backend/.env` для Docker
   менять не нужно: адрес базы, режим и почту задаёт `compose.yaml`.
4. Соберите и запустите:

   ```bash
   docker compose up -d --build
   ```

   Первая сборка занимает несколько минут. Миграции, справочники и банк вопросов
   применяются сами. Тестовых пользователей на стенде нет, если не задан `SEED_DEMO=true`.

| Адрес                          | Что там                            |
| ------------------------------ | ---------------------------------- |
| http://localhost:8080          | приложение                         |
| http://localhost:8080/api/docs | Swagger: все эндпоинты API         |
| http://localhost:8025          | Mailpit: все письма подтверждения  |

```bash
docker compose ps                       # статус контейнеров
docker compose logs -f backend          # логи бэкенда
docker compose up -d --build backend    # пересобрать бэкенд после правок кода
docker compose down                     # остановить, данные сохранятся
docker compose down -v                  # остановить и удалить базу: следующий старт с чистыми демо-данными
```

---

## Вариант 2. Локально

### 1. Инструменты

- Python 3.12+ и [uv](https://docs.astral.sh/uv/getting-started/installation/): `pip install uv`.
- Node.js 20+ (npm входит в комплект).
- PostgreSQL 16: свой или из Docker (следующий шаг).

### 2. База данных

**Проще всего: Postgres и Mailpit из compose.** Нужен корневой `.env` с `POSTGRES_PASSWORD`
(шаг 2 варианта с Docker), затем:

```bash
docker compose up -d postgres mailpit
```

Появится база `fsphack` с пользователем `fspadmin` и паролем из `POSTGRES_PASSWORD` на порту 5432.

**Свой Postgres.** Создайте пользователя и базу от имени суперпользователя (psql, DBeaver, pgAdmin):

```sql
CREATE USER fspadmin WITH PASSWORD 'ваш_пароль';
CREATE DATABASE fsphack OWNER fspadmin;
```

### 3. Настройки бэкенда

```bash
cd backend
cp .env.example .env                    # PowerShell: Copy-Item .env.example .env
```

В `backend/.env` заполните:

```env
APP_ENV=dev
DATABASE_URL=postgresql+asyncpg://fspadmin:ПАРОЛЬ@localhost:5432/fsphack
DATABASE_URL_SYNC=postgresql+psycopg://fspadmin:ПАРОЛЬ@localhost:5432/fsphack
JWT_SECRET=строка от 32 символов: python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Спецсимволы пароля внутри адреса кодируются: `!` → `%21`, `@` → `%40`, `#` → `%23`, `:` → `%3A`.
Например, пароль `Qwerty1!` записывается как `fspadmin:Qwerty1%21@localhost`.

Почту можно не настраивать: без неё ссылка подтверждения появится в логе бэкенда
(см. [Почта](#почта)).

### 4. Бэкенд

```bash
cd backend
uv sync                                         # зависимости в backend/.venv
uv run alembic upgrade head                     # создать таблицы
uv run python -m app.seed --demo                # справочники + демо-аккаунты; повтор ничего не ломает
                                                # без --demo: только справочники и админ из ADMIN_*
uv run uvicorn app.main:app --reload --port 8000
```

Проверка: http://localhost:8000/api/health/ready отвечает `"status":"ok"`.
Swagger: http://localhost:8000/api/docs.

### 5. Фронтенд (во втором терминале)

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173. Запросы к `/api` Vite передаёт на `http://localhost:8000`;
другой адрес бэкенда задаётся переменной `VITE_API_PROXY_TARGET`.

Фронт без бэкенда, на моках:

```bash
VITE_USE_MOCKS=true npm run dev                 # bash
$env:VITE_USE_MOCKS="true"; npm run dev         # PowerShell
```

---

## Почта

После регистрации приходит письмо со ссылкой подтверждения. Пока адрес не подтверждён,
работодатель не может отправлять предложения, а кандидат не виден в поиске. Демо-аккаунты уже
подтверждены.

Куда попадёт письмо, зависит от настроек:

| Настройки                                          | Что происходит                         | Где ссылка                                                  |
| -------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------- |
| `APP_ENV=dev`, пустой `SMTP_HOST` (локально по умолчанию) | письмо не отправляется          | лог бэкенда: строка `email_not_sent`, поле `verification_url` |
| Mailpit (в Docker по умолчанию)                    | письмо ловит Mailpit, наружу не уходит | http://localhost:8025                                       |
| настоящий SMTP                                     | письмо приходит в реальный ящик        | почта получателя (проверьте «Спам»)                         |
| `APP_ENV=prod`, пустой `SMTP_HOST`                 | регистрация отвечает 503               | —                                                           |

Где менять настройки: локально — `backend/.env`, в Docker — корневой `.env` (значения compose
перекрывают `backend/.env`). После изменений перезапустите бэкенд: `--reload` следит только за
кодом, а в Docker выполните `docker compose up -d`, и контейнер пересоздастся.

### Mailpit при локальном запуске

```bash
docker compose up -d mailpit
```

В `backend/.env`:

```env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_SSL=false
SMTP_STARTTLS=false
```

Письма смотрите на http://localhost:8025.

### Настоящая почта

Нужен ящик и **пароль приложения**: обычный пароль от почты по SMTP не принимается. Адрес
отправителя `SMTP_FROM_EMAIL` должен совпадать с ящиком, иначе сервер отклонит письмо.

| Сервис  | `SMTP_HOST`      | `SMTP_PORT` | `SMTP_USE_SSL` | `SMTP_STARTTLS` | Где взять пароль приложения                                           |
| ------- | ---------------- | ----------- | -------------- | --------------- | --------------------------------------------------------------------- |
| Яндекс  | `smtp.yandex.ru` | 465         | `true`         | `false`         | Яндекс ID → Безопасность → Пароли приложений → «Почта»                 |
| Mail.ru | `smtp.mail.ru`   | 465         | `true`         | `false`         | Настройки → Безопасность → Пароли для внешних приложений              |
| Gmail   | `smtp.gmail.com` | 587         | `false`        | `true`          | включите двухэтапную аутентификацию, затем myaccount.google.com/apppasswords |

У Яндекса также включите в настройках почты доступ для почтовых программ.

Пример для Яндекса:

```env
SMTP_HOST=smtp.yandex.ru
SMTP_PORT=465
SMTP_USE_SSL=true
SMTP_STARTTLS=false
SMTP_USERNAME=resonance-team@yandex.ru
SMTP_PASSWORD=пароль_приложения
SMTP_FROM_EMAIL=resonance-team@yandex.ru
```

Ссылка в письме ведёт на `PUBLIC_API_URL`. Это должен быть адрес, который откроется у
получателя: локально `http://localhost:8000`, в Docker `http://localhost:8080` (уже задан), на
сервере — его публичный адрес. Ссылка на `localhost` у жюри не откроется.

### Письмо не пришло

Посмотрите лог бэкенда: локально это терминал с uvicorn, в Docker — `docker compose logs backend`.
При сбое там будет строка `verification_email_failed`, причина в поле `error`:

| В поле `error`                                        | Причина                              | Что сделать                                                     |
| ----------------------------------------------------- | ------------------------------------ | --------------------------------------------------------------- |
| `SMTPAuthenticationError(535, …)`                     | неверный логин или пароль            | нужен пароль приложения; логин — полный адрес ящика             |
| `ConnectionRefusedError`, `TimeoutError`, `gaierror`  | сервер недоступен                    | проверьте `SMTP_HOST` и `SMTP_PORT`; запущен ли Mailpit         |
| `SSLError`, `SMTPServerDisconnected`                  | не та схема шифрования               | порт 465 → `SMTP_USE_SSL=true`, порт 587 → `SMTP_STARTTLS=true` |
| `SMTPSenderRefused`, `SMTPDataError(553, …)`          | отправитель не совпадает с ящиком    | `SMTP_FROM_EMAIL` такой же, как `SMTP_USERNAME`                 |
| вместо неё `email_not_sent`                           | SMTP не настроен                     | см. таблицу в начале раздела                                    |

Кнопка «Отправить ещё раз» в баннере показывает ошибку, если письмо не ушло. Повторно отправить
можно раз в минуту.

---

## Демо-аккаунты

Есть только после `python -m app.seed --demo` (в Docker — `SEED_DEMO=true`) и в режиме
моков фронта. Пароль у всех `demo1234`.

| Email               | Роль         | Кто                                          |
| ------------------- | ------------ | -------------------------------------------- |
| `employer@demo.ru`  | работодатель | Игорь Смирнов, Resonance Labs                |
| `employer2@demo.ru` | работодатель | Ольга Петрова, ТехноСфера                    |
| `candidate@demo.ru` | кандидат     | Анна Ковалёва, Frontend middle, тест 82, ФСП |
| `admin@demo.ru`     | админ        | Админ Resonance                              |

Ещё кандидаты: `elena@`, `maxim@`, `denis@`, `sofia@`, `candidate1@` … `candidate8@demo.ru`.

Сценарий для показа:

1. `employer@demo.ru` → Talent Pool → вакансия «Frontend Engineer (React)». Анна (тест 82)
   стоит выше Елены (тест 91): у Анны полный стек и ФСП, у Елены не хватает навыков и формат
   «офис». У каждого кандидата видны причины.
2. Карточка Анны: контакты закрыты → «Отправить предложение».
3. `candidate@demo.ru` → Предложения → открыть → «Принять».
4. `employer@demo.ru`: в карточке Анны появились контакты, в колокольчике «Оффер принят».
5. Кандидат проходит тест (10 вопросов, есть задачи с кодом) и синхронизирует ФСП.
   Тесты есть для Backend middle и Frontend middle.
6. `admin@demo.ru`: сводка, пользователи (можно заблокировать), вакансии и офферы.

---

## Тесты

```bash
cd backend
uv run pytest tests/unit -q          # без базы
uv run pytest tests/integration -q   # нужна база после upgrade head и seed

cd frontend
npm run test
npm run lint
npm run build
```

Интеграционные тесты создают пользователей и офферы. Гоняйте их на отдельной базе, а не на
демо-стенде: укажите её в `DATABASE_URL` и `DATABASE_URL_SYNC`, затем выполните
`alembic upgrade head` и `python -m app.seed --demo`.

---

## Частые проблемы

| Симптом                                                                 | Что сделать                                                                                              |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `Can't locate revision identified by '…'` при `alembic upgrade head`    | база создана до объединения миграций: пересоздайте её (`DROP DATABASE` + `CREATE DATABASE` или `docker compose down -v`), затем `upgrade head` и `seed` |
| `password authentication failed for user "fspadmin"`                    | неверный пароль в `DATABASE_URL`; спецсимволы закодированы?                                              |
| `Connection refused` на 5432                                            | Postgres не запущен                                                                                      |
| `port is already allocated` / `address already in use`                  | порт занят: 5432 (локальный Postgres мешает compose), 8000, 8080, 5173 или 8025                          |
| бэкенд не стартует, `ValidationError` про `JWT_SECRET`                  | `JWT_SECRET` пустой или короче 32 символов                                                               |
| в консоли Vite `http proxy error … ECONNREFUSED`                        | бэкенд не запущен на :8000                                                                               |
| вход отвечает `429`, «Слишком много запросов»                           | лимит 5 попыток в минуту с одного адреса; для демо `RATE_LIMIT_ENABLED=false`                            |
| регистрация отвечает 503                                                | `APP_ENV=prod` без SMTP, см. [Почта](#почта)                                                             |
| «Тест для категории … пока не готов»                                    | вопросы есть только для Backend middle и Frontend middle                                                 |
| правки в `.env` не применились                                          | перезапустите uvicorn; в Docker выполните `docker compose up -d`                                         |
| `uv: command not found`                                                 | `pip install uv`, затем откройте новый терминал                                                          |
