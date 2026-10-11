# 19. Типичные проблемы

| Симптом | Вероятная причина | Что сделать |
| ------- | ----------------- | ----------- |
| `POSTGRES_PASSWORD` error при compose | нет корневого `.env` | задать пароль латиницей/цифрами |
| Backend unhealthy | БД не готова / JWT_SECRET пуст | `docker compose logs backend`, проверить `.env` |
| `SEED_SKIP` / нет демо-логинов | сид не бежал или БД старая без демо | `down -v` и `up`, или `uv run python -m app.seed` на пустой БД |
| Логин 429 | rate limit с одного NAT | `RATE_LIMIT_ENABLED=false` |
| Регистрация 503 | prod без SMTP | поднять Mailpit или настроить SMTP |
| Письмо не приходит | SMTP/Mailpit | http://localhost:8025; в dev — лог backend |
| CORS ошибки на :5173 | CORS_ORIGINS | добавить `http://localhost:5173` |
| Пустой Talent Pool | нет verified кандидатов под категорию | использовать seed Frontend Middle |
| Оффер 403 EMAIL_NOT_VERIFIED | почта employer | подтвердить через Mailpit |
| Contacts 403 | нет Accept/Apply | пройти сценарий C |
| UI не видит API в Docker | собрали с моками | пересобрать `VITE_USE_MOCKS=false` |
| Vite не проксирует | backend не на 8000 | `VITE_API_PROXY_TARGET` |
| Спецсимволы в пароле БД | ломают URL | percent-encode (`!`→`%21`) |
| ML не влияет на ranking | MATCHER_PROVIDER=baseline | выставить `ml` и URL |
| Windows пути / команды | другой shell | см. PowerShell варианты в `SETUP.md` |

Расширенные заметки по почте и Windows: корневой `SETUP.md`.
