# FSP Talent — UI Kit & Design System

**Версия:** 1.0  
**Стиль:** Minimal Tech / Bento Dashboard  
**Основа:** [брендбук ФСП](https://fsp-russia.ru/press/brandbook/)  
**Шрифты:** [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) + Golos Text  

| Слой | Путь |
|------|------|
| Tokens | `src/styles/global.css` |
| Shared UI | `src/shared/ui/*` |
| Domain UI | `src/entities/ui/*` |
| Living catalog | [`/ui-kit`](/ui-kit) |
| Landing | `src/pages/LandingPage.module.css` |

```ts
import { Button, Input, Badge, Switch, Modal } from '@/shared/ui';
import { MatchScore } from '@/entities/ui/MatchScore';
```

---

## 0. Принципы

1. **Backend owns truth.** Match Score, scores, FSP, contacts — только DTO.
2. **Tokens only.** HEX в компонентах запрещён — только CSS variables.
3. **One system.** Кандидат / работодатель / админ — одна палитра.
4. **FSP ≠ self-reported.** `FSPVerificationBadge` только на данных ФСП.
5. **Domain components are dumb.** Fetch только в pages/hooks.
6. **6 states:** loading · success · empty · error · disabled · action success.
7. **Красный #EC1D35** — фирменный акцент и destructive, не primary CTA.
8. **A11y:** labels, focus ring 3px, keyboard, `prefers-reduced-motion`.

---

## 1. Design tokens (`:root`)

### Brand (ФСП)

| Token | Value |
|-------|-------|
| `--brand-primary` | `#402FFF` |
| `--brand-red` | `#EC1D35` |
| `--brand-light-gray` | `#EDEDED` |
| `--brand-gray` | `#C8C9CA` |
| `--brand-dark` | `#1B1C21` |

### Primary scale

`--primary-50` … `--primary-900` (`#F2F0FF` → `#15105E`), `--primary-500` = brand.

### Surfaces / text / borders / semantic

См. `global.css`: `--background-*`, `--text-*`, `--border-*`, `--success-*`, `--warning-*`, `--error-*`, `--info-*`.

### Spacing (4px grid)

`--space-1` (4) … `--space-16` (64).

### Radius

| Token | Value | Use |
|-------|-------|-----|
| `--radius-icon` / `--radius-badge` | 8px | chips, badges |
| `--radius-control` | 12px | button, input, compact card |
| `--radius-card` | 16px | bento |
| `--radius-hero` / `--radius-modal` | 20px | hero, modal |
| `--radius-pill` | 999px | progress |

### Shadows

`--shadow-card`, `--shadow-card-hover`, `--shadow-dropdown`, `--shadow-modal`.

### Layout

`--sidebar-width: 244px` · `--topbar-height: 72px` · `--content-max: 1600px` · `--ease: cubic-bezier(0.2, 0, 0, 1)`.

### Typography

| Token | Font |
|-------|------|
| `--display` | JetBrains Mono (H1–H3, KPI, code) |
| `--font` | Golos Text (UI body) |

Aliases для legacy: `--accent`, `--ink`, `--surface`, `--radius` → map на FSP tokens.

---

## 2. Shared UI (`@/shared/ui`)

| Component | Notes |
|-----------|--------|
| `Button` | `primary \| secondary \| outline \| ghost \| danger` · `sm \| md \| lg` |
| `Input` / `Textarea` / `Select` | label сверху, error 12px под полем |
| `Checkbox` / `Radio` / `Switch` | 18px / 40×24 |
| `Badge` | `default \| accent \| fsp \| warn \| success \| danger` |
| `Card` | `default \| compact \| hero` · optional `to` |
| `Tabs` / `Modal` / `ProgressBar` | |
| `Loader` / `Skeleton` / `EmptyState` / `ErrorState` | |

Кнопки: height 36/44/48, radius 12, Golos 14/600.  
Focus: `outline: 3px solid var(--primary-200)`.

---

## 3. Layout chrome

Классы в `global.css`:

- `.app-shell` · `.app-sidebar` · `.nav` · `.app-main`
- `.topbar` · `.topbar-user` · `.topbar-avatar`
- `.page` · `.page-header` · `.section-card`
- `.grid-2` / `.grid-3` · `.stack` · `.row` · `.bento` utilities по мере нужды

Sidebar: item height 44, radius 10, active = `--background-selected`.

---

## 4. Domain UI (`@/entities/ui`)

`CandidateCard`, `CandidateProfileView`, `VacancyCard`, `OfferCard`, `OfferForm`, `MatchScore`, `SkillRadar`, `SkillBadge`, `GradeBadge`, `FSPVerificationBadge`, `FSPAchievementCard`, `TestQuestionView`, `TestResultView`, `SalaryRange`, …

Props = DTO. Skill chips: `.skillChip` (`#F2F0FF` / `#3324E6`).

---

## 5. Do / Don't

**Do:** tokens · Lucide only · bento 16px · status = color + text · tabular-nums на KPI.

**Don't:** neon gradients · random radii · Material/FA/emoji icons · Verified без источника · second palette per role · fixed-height cards that clip content.

---

## 6. Acceptance

- `/ui-kit` отражает актуальную систему.
- Все экраны на FSP tokens.
- Кнопки/формы/карточки/sidebar/topbar единообразны.
- Нет горизонтального overflow страницы.
- Функциональность и API-контракты не сломаны.

**Visual source of truth:** http://localhost:5173/ui-kit
