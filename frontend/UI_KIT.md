# LCT Resonance — UI Kit

Подробная спецификация дизайн-системы и компонентов клиентской части.  
Источник истины в коде:

| Слой | Путь |
|------|------|
| Tokens / layout utilities | `src/styles/global.css` |
| Base components | `src/shared/ui/*` |
| Domain components | `src/entities/ui/*` |
| Landing (отдельная поверхность) | `src/pages/LandingPage.module.css` |

Импорт базовых:

```ts
import { Button, Input, Badge, Modal, Loader } from '@/shared/ui';
```

Импорт предметных — напрямую из `@/entities/ui/...`.

---

## 0. Принципы

1. **Backend owns truth.** Match Score, test scores, FSP verification, contacts access — только отображение DTO.
2. **No false claims.** «навык не указан в профиле» ≠ «кандидат не умеет».
3. **FSP ≠ self-reported.** `FSPVerificationBadge` только на данных ФСП.
4. **Domain components are dumb.** Props = DTO/view-model. Fetch только в pages/hooks.
5. **Every data view has 6 states:** loading · success · empty · error · action disabled · action success.
6. **Cards only for interaction containers** (списки кандидатов/вакансий/офферов). Hero лендинга — без карточек.
7. **A11y minimum:** label ↔ control, focus ring, `aria-*` на modal/progress/QR, `prefers-reduced-motion` на лендинге.

---

## 1. Design tokens

### 1.1. Color

| Token | Value | Usage |
|-------|-------|--------|
| `--ink` | `#14201c` | основной текст |
| `--ink-muted` | `#5a655f` | вторичный текст, `.muted` |
| `--surface` | `#f4f0e8` | бумажная поверхность |
| `--surface-2` | `#ebe4d6` | вторичный фон |
| `--line` | `rgba(20,32,28,.12)` | бордеры |
| `--accent` | `#0d7a5f` | primary CTA, progress |
| `--accent-soft` | `#d7efe6` | soft fill, nav active |
| `--accent-ink` | `#064c3b` | текст на soft accent |
| `--success` | `#0f766e` | positive reasons, accepted |
| `--warn` | `#b45309` | warnings, viewed |
| `--danger` | `#b42318` | errors, decline, blocked |
| `--fsp` | `#1d4ed8` | FSP verified |
| `--fsp-soft` | `#dbeafe` | FSP blocks |

**Landing-only palette** (scoped в `LandingPage.module.css`, light/dark через `[data-theme]`):

| Role | Light | Dark |
|------|-------|------|
| bg | `#f7f5f0` | `#0e1612` |
| bg-alt | `#eef5ed` | `#121c17` |
| surface | `#ffffff` | `#1c2b23` |
| ink | `#101210` | `#f4f7f5` |
| muted | `#606b64` | `#a8bdb0` |
| accent | `#2f8a57` | `#5cbc7d` |
| accent-deep | `#185c3d` | `#1f4d35` |
| accent-fill | `#ddebdd` | `#24382c` |
| CTA primary | accent-deep + white | same |
| CTA secondary | accent-fill / accent-deep text | same |

Hero art: `/resonance_hero.svg`. Dock + theme toggle — landing-only.

### 1.2. Typography

| Token / role | Font | Size / notes |
|--------------|------|----------------|
| `--font` | **DM Sans** | UI, body, controls (app) |
| `--display` | **Instrument Serif** | app h1–h3, match score, stats |
| Landing sans | **Manrope** | landing body |
| Landing display | **Syne** 800 | landing hero / section titles |
| `h1` | display | `clamp(2rem, 4vw, 3rem)` |
| `h2` | display | `clamp(1.5rem, 3vw, 2rem)` |
| body | DM Sans | 1rem / line-height 1.5 |
| label | DM Sans 600 | 0.85rem |
| badge | DM Sans 600 | 0.8rem |

### 1.3. Radius, shadow, spacing

| Token | Value |
|-------|-------|
| `--radius` | `14px` — cards, sections |
| `--radius-sm` | `10px` — inputs |
| pill | `999px` — buttons, badges, tabs, nav |
| `--shadow` | `0 18px 50px rgba(10,16,20,.18)` |
| page max | `1120px` |
| stack gap | `1rem` |
| row gap | `0.75rem` |

### 1.4. Layout utilities (global classes)

| Class | Purpose |
|-------|---------|
| `.app-shell` | topbar + main |
| `.topbar` / `.brand` / `.nav` | кабинетная шапка |
| `.page` / `.page-header` | контентная колонка |
| `.stack` / `.row` | flex column / row |
| `.grid-2` / `.grid-3` | adaptive grids (→1 col ≤800px) |
| `.section-card` | контентный блок |
| `.fsp-block` | визуально отделённый FSP-контейнер |
| `.filters` | auto-fit filter grid |
| `.stats` / `.stat` | dashboard metrics |
| `.match-box` / `.match-score` | Match Score container |
| `.reason-list` / `.pos` / `.neg` | match reasons |
| `.hidden-contacts` | contacts locked state |
| `.auth-page` / `.auth-card` | login/register |
| `.muted` | secondary text |

---

## 2. Базовые компоненты (`@/shared/ui`)

### 2.1. Button

```tsx
<Button variant="primary" type="button" disabled={false}>Сохранить</Button>
```

| Prop | Type | Default | Notes |
|------|------|---------|-------|
| `variant` | `'primary' \| 'secondary' \| 'danger' \| 'ghost'` | `primary` | |
| `...button` | native | | `type` обязателен явно в формах |

| Variant | Когда |
|---------|--------|
| `primary` | главный CTA экрана / submit |
| `secondary` | отмена, назад, вторичное действие |
| `danger` | decline, block, удаление |
| `ghost` | закрытие modal, низкий акцент |

**States:** default · hover · disabled (`opacity: .5`).

---

### 2.2. Input / Textarea / Select

Общий паттерн поля:

```
[label]
[control]
[error?]
```

```tsx
<Input label="Email" name="email" type="email" error={errors.email?.message} />
<Textarea label="О себе" name="about" />
<Select
  label="Грейд"
  name="grade"
  options={[{ value: 'middle', label: 'Middle' }]}
  allowEmpty
  emptyLabel="Все"
/>
```

| Prop | Notes |
|------|--------|
| `label` | обязателен; `htmlFor` = `id \|\| name \|\| slug(label)` |
| `error` | красный текст под контролом |
| `allowEmpty` | только Select — пустая опция для фильтров |

**Focus:** outline `2px` accent soft + border accent.

---

### 2.3. Checkbox

```tsx
<Checkbox label="Выбрать для сравнения" checked={on} onChange={...} />
```

Используется в Talent Pool для multi-select compare (не как визуальный «pill cluster»).

---

### 2.4. Badge

```tsx
<Badge tone="fsp">Подтверждено ФСП</Badge>
```

| Tone | Смысл |
|------|--------|
| `default` | нейтральный (грейд raw) |
| `accent` | readiness, skills soft |
| `fsp` | **только** FSP verified |
| `success` | accepted, confirmed, active |
| `warn` | viewed, not confirmed |
| `danger` | declined, blocked |

---

### 2.5. Card

```tsx
<Card to="/employer/candidates/cand-1">...</Card>
<Card>...</Card> // static
```

| Prop | Notes |
|------|--------|
| `to?` | если есть — `Link` + hover lift/shadow |
| `className` | доп. (например `fsp-block`) |

**Правило:** Card = контейнер кликабельной сущности списка. Не для hero.

---

### 2.6. Tabs

```tsx
<Tabs
  tabs={[{ id: 'a', label: 'A' }, { id: 'b', label: 'B' }]}
  value={tab}
  onChange={setTab}
/>
```

`role="tablist"` / `aria-selected`. Active = ink fill.

---

### 2.7. Modal

```tsx
<Modal open={open} title="Новое предложение" onClose={() => setOpen(false)}>
  <OfferForm ... />
</Modal>
```

- backdrop click → close  
- stopPropagation на dialog  
- `role="dialog"` + `aria-modal`  
- header: title + ghost ✕

---

### 2.8. Loader / Skeleton

```tsx
<Loader label="Ищем кандидатов..." />
<Skeleton height={72} width="100%" />
```

Loader — spinner + optional label.  
Skeleton — shimmer для FSP sync и длинных списков.

---

### 2.9. ProgressBar

```tsx
<ProgressBar value={2} max={3} />
```

`role="progressbar"` + `aria-valuenow/min/max`.  
Используется в testing session.

---

### 2.10. EmptyState / ErrorState

```tsx
<EmptyState
  title="Подходящие кандидаты не найдены"
  description="Измените фильтры."
  action={<Button>...</Button>}
/>

<ErrorState
  title="Ошибка поиска"
  description={message}
  onRetry={() => refetch()}
/>
```

| Component | Когда |
|-----------|--------|
| `EmptyState` | 200 + пустой список / нет сущности |
| `ErrorState` | network/API fail; `onRetry` опционален |

---

## 3. Предметные компоненты (`@/entities/ui`)

> Все принимают готовые DTO. **Не** ходят в API.

### 3.1. SkillBadge / GradeBadge

```tsx
<SkillBadge skill="React" />
<GradeBadge grade="middle" />
```

- Skill → `Badge tone="accent"`  
- Grade → `Badge` + `formatGrade()` (`Intern…Lead`)

**Запрет:** не вешать `tone="fsp"` на skill/grade из профиля.

---

### 3.2. FSPVerificationBadge

```tsx
<FSPVerificationBadge />                    // «Подтверждено ФСП»
<FSPVerificationBadge label="FSP Verified" />
```

Только рядом с FSP achievements / hasFsp flag на карточке кандидата.

---

### 3.3. FSPAchievementCard

Поля карточки:

| Field | UI |
|-------|-----|
| `title` | h3 |
| `discipline` · `date` · `placeOrResult` | subtitle |
| `participantRole` / `sportRank` | muted meta |
| always | `FSPVerificationBadge` |

Обёртка: `Card` + класс `fsp-block` (голубой градиент).

---

### 3.4. SalaryRange

```tsx
<SalaryRange from={280000} to={320000} currency="RUB" />
// → «280 000–320 000 ₽»
```

Обязательно показывать в `OfferCard` / `OfferForm` (зарплата не может быть «спрятана»).

---

### 3.5. MatchReason / MatchScore

```tsx
<MatchScore match={candidateMatchDto} />
```

Структура:

```
Match {score}%
Почему подходит:
  ✓ positive reason
  • non-positive reason
Не указано в профиле:
  Jest — навык не указан в профиле
```

| Copy rule | Allowed | Forbidden |
|-----------|---------|-----------|
| missing skill | «не указан в профиле» | «не умеет», «не знает» |
| score source | Backend `match.score` | клиентский пересчёт |

---

### 3.6. CandidateCard

Список Talent Pool / Shortlist / Compare picker.

Показывает:

- имя, specialization · grade  
- top-5 skills  
- readiness badge  
- `FSP Verified` если `hasFspAchievements`  
- Match % + 1–2 positive reasons (если `match` есть)  

`to` → полный профиль.

---

### 3.7. CandidateProfileView

```tsx
<CandidateProfileView
  mode="self" | "employer"
  profile={dto}
  achievements={fsp[]}
  match={optional}
/>
```

| Block | self | employer |
|-------|------|----------|
| about / skills / preferences | ✓ | ✓ |
| claimed grade ≠ test result | раздельно | раздельно |
| MatchScore | ✗ | ✓ if `match` |
| FSP achievements | ✓ | ✓ |
| disclaimer self≠FSP | ✓ | ✓ |
| contacts | вне компонента (page) | page + API gate |

---

### 3.8. VacancyCard

```tsx
<VacancyCard vacancy={v} to="/employer/vacancies/id" />
<VacancyCard vacancy={v} /> // admin list, non-link
```

Title, status badge, specialization · grade · format, **SalaryRange**.

---

### 3.9. OfferCard / OfferForm

**OfferCard:** company, position, salary (явная), format, message, date, status badge.

Status → tone:

| Status | Tone | Label |
|--------|------|-------|
| `new` | accent | Новое |
| `viewed` | warn | Просмотрено |
| `accepted` | success | Принято |
| `declined` | danger | Отклонено |

**OfferForm:** RHF + Zod; блок «Зарплатная вилка в предложении» всегда видим до submit.

---

### 3.10. TestQuestion / TestResult

**TestQuestion:** radio options, progress externally, CTA «Далее» / «Завершить».  
На клиенте **нет** `correctOptionId`.

**TestResult:**

```
Заявленный уровень: Middle
Результат тестирования: 82/100
Уровень подтвержден | не подтвержден
[Retest badge if isRetest]
```

Claimed grade и score — **отдельные** строки.

---

### 3.11. SkillRadar (P2)

```tsx
<SkillRadar radar={{ candidateId, axes: [{ skill, score }] }} size={280} />
```

- SVG radar по осям Backend  
- подпись: «Оценки рассчитаны на Backend/ML…»  
- empty: «Нет данных для Skill Radar.»  
- `data-testid="skill-radar"`

---

## 4. Обязательные UI-состояния (data views)

Для Talent Pool, FSP, Offers, Vacancies, Profile, Admin lists, Analytics:

| State | Component / pattern |
|-------|---------------------|
| Loading | `<Loader />` или `<Skeleton />` |
| Success | контент |
| Empty | `<EmptyState />` |
| Error | `<ErrorState onRetry />` |
| Action disabled | Button `disabled` + pending label («Сохраняем…») |
| Action success | inline banner / status text («Предложение отправлено», «Черновик подставлен») |

### Канонические copy (RU)

| Context | Copy |
|---------|------|
| FSP loading | Получаем данные ФСП... |
| FSP success | Найдено N подтвержденных достижений. |
| FSP empty | Достижения ФСП пока не найдены. |
| FSP error | Не удалось получить данные ФСП. Попробуйте выполнить синхронизацию позже. |
| Contacts locked | Контактные данные скрыты / Контакты будут доступны после того, как кандидат примет предложение. |
| Talent empty | Подходящие кандидаты не найдены. |

---

## 5. Паттерны страниц

### 5.1. Page chrome

```
topbar[ brand | nav(role) | user + logout ]
page[
  page-header[ title+subtitle | actions ]
  content
]
```

### 5.2. Filters bar

`.filters.section-card` + debounce 300ms на текстовые поля → query → Backend.

### 5.3. Auth

`.auth-page` > `.auth-card` > form stack + `.demo-hint`.

### 5.4. Landing (отдельная поверхность)

Не использовать app `Button`/`Card` в hero.
Первый viewport: brand (logo) · headline · CTA pair · bars visual · subtitle · product peek.
Секции: bento how-it-works · roles · features (mode toggle) · CTA band · footer.
Chrome: fixed header, floating dock (theme + anchors), light/dark.
Motion: `brandIn`, `fadeUp`, `lineIn`, `artIn`, `scrollPulse`.
Breakpoints: 480 / 640 / 768 / 1024 / 1280 + `safe-area-inset`.
Respect `prefers-reduced-motion`.
Спека в UI: [`/ui-kit`](/ui-kit).

---

## 6. Иконография и маркеры

Иконок-пакета нет (намеренно). Маркеры — текстовые/CSS:

| Marker | Where |
|--------|--------|
| `✓` | positive MatchReason (`.pos`) |
| `•` | non-positive MatchReason (`.neg`) |
| FSP blue block | verified achievements |
| Dashed box | hidden contacts |
| Spinner | Loader |
| Shimmer | Skeleton |

---

## 7. Доступность (чеклист)

- [ ] У каждого Input/Select/Textarea есть связанный `<label>`
- [ ] Modal: Escape/backdrop close, focusable close button
- [ ] ProgressBar: aria-valuenow
- [ ] Tabs: aria-selected
- [ ] Disabled кнопки не кликабельны во время mutation
- [ ] Контраст текста на accent/landing CTA достаточен
- [ ] Landing animations отключаются при reduced motion

---

## 8. Что нельзя делать в UI

| Anti-pattern | Почему |
|--------------|--------|
| Считать Match/test на клиенте | нарушает границы ТЗ |
| Помечать skill/grade как FSP Verified | ложная верификация |
| «Кандидат не знает X» | запрещённый копирайт |
| Показывать contacts без успешного GET contacts | security |
| Correct answers до finish теста | spoiler / cheat |
| Карточки/stats в первом viewport лендинга | hero budget |
| Смешивать landing dark tokens с app chrome без scope | визуальный шум |

---

## 9. Карта компонентов → экраны

| Экран | Компоненты |
|-------|------------|
| Login / Register | Input, Select, Button, auth-card |
| Candidate profile | CandidateProfileView, SkillRadar, FSPAchievementCard, Button |
| FSP | Skeleton, Loader, Empty/Error, FSPAchievementCard, Button |
| Offers inbox/detail | OfferCard, Button(danger/primary), SalaryRange |
| Testing | ProgressBar, TestQuestion, TestResult, Badge |
| Talent Pool | filters, Checkbox, CandidateCard, Empty/Error/Loader, Button |
| Candidate detail (employer) | hidden-contacts, CandidateProfileView, MatchScore, SkillRadar, Modal+OfferForm |
| Vacancies | VacancyCard, Offer-like forms, SalaryRange |
| Compare | table + SkillRadar × N |
| Employer dashboard | stats + analytics section |
| Admin | stats, Badge status, Button danger/secondary, OfferCard, VacancyCard |
| Public passport | QrCode, CandidateProfileView, SkillRadar, FSPVerificationBadge |
| Landing | LandingPage.module.css only (scoped) |

---

## 10. Расширение UI-kit (как добавлять)

1. **Атом/молекула без домена** → `shared/ui` + export из `index.ts` + стили в `ui.module.css`.  
2. **Доменный виджет** → `entities/ui`, props = DTO, без fetch.  
3. **Обновить этот файл:** props table + states + где используется.  
4. **Тест:** минимум render + ключевой copy/a11y assertion (см. `*.test.tsx` рядом).  
5. Не плодить вторую палитру — только tokens из `:root` (landing — исключение со scoped module).

---

## 11. Quick reference — варианты

### Button
`primary` · `secondary` · `danger` · `ghost`

### Badge
`default` · `accent` · `fsp` · `success` · `warn` · `danger`

### Offer status → Badge tone
`new→accent` · `viewed→warn` · `accepted→success` · `declined→danger`

### Work format labels
`remote→Удалённо` · `hybrid→Гибрид` · `office→Офис`

### Readiness labels
`actively_looking→Активно ищу работу`  
`open_to_offers→Открыт к предложениям`  
`not_looking→Не рассматриваю предложения`

---

*UI Kit синхронизирован с реализацией на ветке `frontend-dev`. При расхождении с кодом — править код или этот документ в том же PR.*
