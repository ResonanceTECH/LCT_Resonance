# 23. Инструкция по сдаче

Организаторы не предоставляют инфраструктуру. Проверяющий должен либо открыть рабочий стенд, либо поднять решение локально.

---

## 1. Что сдаём

| Артефакт | Где | Статус |
| -------- | --- | ------ |
| Репозиторий с исходниками | git remote команды | укажите актуальный URL при сдаче |
| Документация Markdown | каталог `docs/` + README | создана |
| Единый том | `docs/FINAL_PROJECT_DOCUMENTATION.md` | создан |
| PDF / DOCX | — | экспорт инструментов в среде агента не найден (нет pandoc/weasyprint); экспортируйте MD→PDF локально |
| Презентация | — | URL не указан в репо |
| Видео | — | URL не указан в репо |
| Публичный стенд | Render/Vercel заготовки | проверенный URL добавить вручную |

---

## 2. Порядок проверки для жюри

1. Прочитать `README.md` (1–2 минуты) и `docs/17_DEMO_SCENARIOS.md`.
2. Запустить: `docker compose up -d --build` (нужны корневой `.env` с `POSTGRES_PASSWORD` и `backend/.env` с `JWT_SECRET`).
3. Открыть http://localhost:8080
4. Войти `employer@demo.ru` / `demo1234` → Talent Pool → score и причины.
5. Войти `candidate@demo.ru` / `demo1234` → офферы → Accept.
6. Снова employer → контакты открыты.
7. Swagger: http://localhost:8080/api/docs
8. Письма: http://localhost:8025
9. При необходимости — полный том `FINAL_PROJECT_DOCUMENTATION.md`.

---

## 3. Демо-доступ (безопасно)

Пароль стенда: `demo1234`  
Аккаунты: `admin@demo.ru`, `employer@demo.ru`, `employer2@demo.ru`, `candidate@demo.ru`, и другие `@demo.ru` из seed.

Не прилагать к сдаче файлы `.env` с боевыми секретами.

---

## 4. Экспорт в PDF (рекомендация команде)

На машине с pandoc:

```bash
pandoc docs/FINAL_PROJECT_DOCUMENTATION.md -o FSP_Talent_Documentation.pdf \
  --from markdown --toc --toc-depth=3 -V lang=ru
```

Либо открыть MD в VS Code / Typora / Word и сохранить как PDF/DOCX.  
Вставить `docs/assets/architecture/architecture.jpg` в раздел архитектуры при экспорте.
