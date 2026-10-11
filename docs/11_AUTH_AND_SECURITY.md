# 11. Авторизация и безопасность

Юридическое соответствие 152-ФЗ **не утверждается** — реализованы технические меры (согласия, минимизация контактов, RBAC). Полноценный security audit не проводился.

---

## 1. Реализованные меры

| Мера | Реализация |
| ---- | ---------- |
| Регистрация email+password | `POST /auth/register` |
| Подтверждение email | токен (hash в БД), письмо SMTP/Mailpit, HTML confirm |
| Пароли | Argon2id (`hash_password` / `verify_password_async`) |
| Access JWT | HS256, TTL 480 мин, claims sub/role/sid |
| Refresh | HttpOnly cookie path `/api/auth`, rotation, reuse detection |
| RBAC | роли candidate / employer / admin на API |
| Rate limit | login/register/resend/offers |
| Контакты | отдельный endpoint + unlock rules |
| Согласия | таблица consents + версия `CONSENT_VERSION` |
| Блокировка | admin status → revoke sessions |
| Prod hardening | `APP_ENV=prod`: нет X-Verification-Token в ответах; Secure cookie |

Frontend хранит access token в `sessionStorage` (`lct_access_token`). Refresh-потока в UI нет — полагается на длинный access TTL.

---

## 2. Матрица видимости данных

| Данные | Сам кандидат | Другой кандидат | Работодатель до согласия | Работодатель после Accept/Apply | Admin |
| ------ | ------------ | --------------- | ------------------------ | ------------------------------- | ----- |
| Email аккаунта | да | нет | нет через contacts | да (contacts API) | да (users) |
| Телефон / контакты профиля | да | нет | 403 CONTACTS_LOCKED | да | опосредованно |
| Профиль без контактов | да | нет (нет API списка для candidate) | да (Talent Pool / detail) | да | да |
| Результаты теста (score) | да | нет | да (в match/profile) | да | assessments |
| Достижения ФСП | да | нет | да | да | — |
| Офферы | свои | нет | свои исходящие | — | все |
| Правильные ответы теста | нет на FE | нет | нет | нет | нет в UI |

«Согласие» на контакты в unlock-логике = принятие оффера или отклик (application), не отдельный checkbox «показать телефон работодателю X». Поле `contacts_visibility` существует в профиле; фактический gate contacts API завязан на offer/application.

---

## 3. Правила доступа API (кратко)

- Кандидат не может читать чужие профили Talent Pool.
- Employer без verified email не создаёт офферы (`EMAIL_NOT_VERIFIED`).
- Кандидат без verified email не виден в pool.
- Admin API только роль admin.

---

## 4. Секреты

Не публиковать: содержимое `.env`, реальные `JWT_SECRET`, SMTP пароли, Neon URL с credentials.  
В документации допустим только демо-пароль стенда `demo1234` для `@demo.ru` аккаунтов.
