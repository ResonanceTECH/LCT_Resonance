# 20. Ограничения MVP и roadmap

## 1. Текущие ограничения

| Ограничение | Причина | Влияние | План |
| ----------- | ------- | ------- | ---- |
| Нет официального API ФСП | не выдано организаторами | только mock/stub | RealFSPAdapter + контракт реестра |
| Демо-достижения ФСП | fixtures JSON | нельзя заявлять официальную верификацию | подключение к реестру |
| MSW существует | параллельная разработка FE | риск путаницы «моки = прод» | в compose моки выключены по умолчанию |
| Ограниченный банк заданий | срок хакатона | не все spec×grade equally rich | расширить generators/blueprint |
| Ограниченные специализации | MVP taxonomy 7 | не весь ИТ-рынок | добавить каталог |
| Синтетика для matching | нет gold dataset | нет Precision@K | собрать разметку, offline eval |
| Нет embeddings | осознанный выбор explainability | слабее семантика текстов | опциональный semantic rerank |
| PDF резюме import/export | не реализовано | паспорт = web page | reportlab/weasyprint |
| Keycloak | не внедрён | локальный JWT | OIDC provider |
| Admin categories edit | UI read-only | правки через seed/SQL | CRUD админки |
| Rate limit in-memory | простота | не shared across replicas | Redis |
| Адаптив mobile | необязателен ТЗ | UX на телефоне вторичен | доработать CSS |
| Публичный URL стенда | не зафиксирован в репо | жюри нужен compose или добавить URL | Render+Vercel |

---

## 2. Roadmap (не текущее состояние)

- Реальная интеграция с реестром ФСП и статусами проверки.
- Keycloak / OIDC вместо локального JWT.
- ATS-интеграции (экспорт офферов/кандидатов).
- Расширение специализаций и банка заданий.
- Карьерные рекомендации / Career Growth.
- Trusted Verification третьей стороной.
- Semantic matching как доп. сигнал при сохранении reasons.
- Полноценный PDF Career Passport.
- Горизонтальное масштабирование и общий rate-limit store.

Не смешивать пункты roadmap с колонкой «реализовано» в других документах.
