import { useEffect, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Bell,
  CheckCircle2,
  Info,
  LayoutDashboard,
  Search,
  Users,
  Briefcase,
  AlertTriangle,
} from 'lucide-react';
import { CandidateCard } from '@/entities/ui/CandidateCard';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { FSPAchievementCard } from '@/entities/ui/FSPAchievementCard';
import { FSPVerificationBadge } from '@/entities/ui/FSPVerificationBadge';
import { GradeBadge } from '@/entities/ui/GradeBadge';
import { MatchScore } from '@/entities/ui/MatchScore';
import { OfferCard } from '@/entities/ui/OfferCard';
import { OfferForm } from '@/entities/ui/OfferForm';
import { SalaryRange } from '@/entities/ui/SalaryRange';
import { SkillBadge } from '@/entities/ui/SkillBadge';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { TestQuestionView } from '@/entities/ui/TestQuestion';
import { TestResultView } from '@/entities/ui/TestResult';
import { VacancyCard } from '@/entities/ui/VacancyCard';
import {
  computeMatch,
  computeSkillRadar,
  fspByCandidate,
  offers,
  profiles,
  testQuestions,
  vacancies,
} from '@/mocks/fixtures';
import {
  Badge,
  Button,
  Card,
  Checkbox,
  EmptyState,
  ErrorState,
  Input,
  Loader,
  Modal,
  ProgressBar,
  Radio,
  Select,
  Skeleton,
  Switch,
  Tabs,
  Textarea,
} from '@/shared/ui';
import styles from './UiKitPage.module.css';

const NAV = [
  { id: 'foundations', label: 'Foundations' },
  { id: 'typography', label: 'Typography' },
  { id: 'buttons', label: 'Buttons' },
  { id: 'forms', label: 'Forms' },
  { id: 'feedback', label: 'Feedback' },
  { id: 'badges', label: 'Badges & chips' },
  { id: 'layout', label: 'Layout' },
  { id: 'tables', label: 'Tables' },
  { id: 'domain', label: 'Domain' },
  { id: 'match', label: 'Match & Radar' },
  { id: 'testing', label: 'Testing' },
  { id: 'offer', label: 'Offer form' },
  { id: 'landing', label: 'Landing' },
  { id: 'rules', label: 'Rules' },
] as const;

const BRAND_COLORS = [
  { name: 'brand-primary', value: '#402FFF', varName: '--brand-primary' },
  { name: 'brand-red', value: '#EC1D35', varName: '--brand-red' },
  { name: 'brand-light-gray', value: '#EDEDED', varName: '--brand-light-gray' },
  { name: 'brand-gray', value: '#C8C9CA', varName: '--brand-gray' },
  { name: 'brand-dark', value: '#1B1C21', varName: '--brand-dark' },
] as const;

const PRIMARY_SCALE = [
  { name: 'primary-50', value: '#F2F0FF', varName: '--primary-50' },
  { name: 'primary-100', value: '#E6E1FF', varName: '--primary-100' },
  { name: 'primary-200', value: '#CEC5FF', varName: '--primary-200' },
  { name: 'primary-300', value: '#AB9EFF', varName: '--primary-300' },
  { name: 'primary-400', value: '#796AFF', varName: '--primary-400' },
  { name: 'primary-500', value: '#402FFF', varName: '--primary-500' },
  { name: 'primary-600', value: '#3324E6', varName: '--primary-600' },
  { name: 'primary-700', value: '#271BB8', varName: '--primary-700' },
  { name: 'primary-800', value: '#1D168C', varName: '--primary-800' },
  { name: 'primary-900', value: '#15105E', varName: '--primary-900' },
] as const;

const SURFACE_COLORS = [
  { name: 'background-page', value: '#F7F7FA', varName: '--background-page' },
  { name: 'background-card', value: '#FFFFFF', varName: '--background-card' },
  { name: 'background-secondary', value: '#F1F1F5', varName: '--background-secondary' },
  { name: 'background-hover', value: '#F0EEFF', varName: '--background-hover' },
  { name: 'background-selected', value: '#EAE6FF', varName: '--background-selected' },
  { name: 'text-primary', value: '#1B1C21', varName: '--text-primary' },
  { name: 'text-secondary', value: '#565966', varName: '--text-secondary' },
  { name: 'text-tertiary', value: '#858895', varName: '--text-tertiary' },
  { name: 'border-default', value: '#E2E3E9', varName: '--border-default' },
  { name: 'border-subtle', value: '#ECECF1', varName: '--border-subtle' },
  { name: 'border-hover', value: '#B9B0FF', varName: '--border-hover' },
  { name: 'border-focus', value: '#402FFF', varName: '--border-focus' },
] as const;

const SEMANTIC_COLORS = [
  { name: 'success-main', value: '#16834A', varName: '--success-main' },
  { name: 'warning-main', value: '#A9650C', varName: '--warning-main' },
  { name: 'error-main', value: '#D8273C', varName: '--error-main' },
  { name: 'info-main', value: '#2764C5', varName: '--info-main' },
] as const;

const SPACES = [
  { token: 'space-1', px: 4 },
  { token: 'space-2', px: 8 },
  { token: 'space-3', px: 12 },
  { token: 'space-4', px: 16 },
  { token: 'space-5', px: 20 },
  { token: 'space-6', px: 24 },
  { token: 'space-8', px: 32 },
  { token: 'space-10', px: 40 },
  { token: 'space-12', px: 48 },
  { token: 'space-16', px: 64 },
] as const;

const RADII = [
  { token: 'radius-icon / badge', value: '8px', css: '8px' },
  { token: 'radius-control', value: '12px', css: '12px' },
  { token: 'radius-card', value: '16px', css: '16px' },
  { token: 'radius-hero / modal', value: '20px', css: '20px' },
  { token: 'radius-pill', value: '999px', css: '999px' },
] as const;

function Section({
  id,
  title,
  hint,
  children,
}: {
  id: string;
  title: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={styles.section} aria-labelledby={`${id}-heading`}>
      <div className={styles.sectionHead}>
        <h2 id={`${id}-heading`}>{title}</h2>
        {hint ? <p className={styles.sectionHint}>{hint}</p> : null}
      </div>
      {children}
    </section>
  );
}

function Canvas({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className={styles.canvas}>
      <p className={styles.canvasLabel}>{label}</p>
      {children}
    </div>
  );
}

function SwatchGrid({
  items,
}: {
  items: readonly { name: string; value: string; varName: string }[];
}) {
  return (
    <div className={styles.swatches}>
      {items.map((c) => (
        <div key={c.name} className={styles.swatch}>
          <div className={styles.swatchChip} style={{ background: c.value }} />
          <div className={styles.swatchMeta}>
            <span className={styles.swatchName}>{c.name}</span>
            <span className={styles.swatchValue}>{c.varName}</span>
            <span className={styles.swatchValue}>{c.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export function UiKitPage() {
  const [tab, setTab] = useState('overview');
  const [modalOpen, setModalOpen] = useState(false);
  const [checked, setChecked] = useState(true);
  const [switchOn, setSwitchOn] = useState(true);
  const [radioVal, setRadioVal] = useState('remote');
  const [activeNav, setActiveNav] = useState<string>('foundations');
  const [selectedOption, setSelectedOption] = useState<string | undefined>('a');

  const profile = profiles[0];
  const match = computeMatch(profile.id, vacancies[0]?.id ?? 'vac-1');
  const radar = computeSkillRadar(profile.id);
  const talentItem = { ...profile, match };
  const achievement = fspByCandidate[profile.id]?.[0];
  const question = testQuestions[0];

  useEffect(() => {
    const ids = NAV.map((item) => item.id);
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        let current = ids[0];
        for (const id of ids) {
          const el = document.getElementById(id);
          if (!el) continue;
          if (el.getBoundingClientRect().top - 120 <= 0) current = id;
        }
        setActiveNav(current);
      });
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  return (
    <div className={styles.page} data-testid="ui-kit-page">
      <header className={styles.topbar}>
        <div className={styles.brandBlock}>
          <img className={styles.brandLogo} src="/fsp-logo.svg" alt="ФСП" />
          <div className={styles.brandText}>
            <div className={styles.brand}>FSP Talent · UI Kit</div>
            <p className={styles.brandMeta}>Design system v1.0 · Minimal Tech / Bento</p>
          </div>
        </div>
        <div className={styles.topActions}>
          <Link to="/">
            <Button type="button" variant="ghost" size="sm">
              На лендинг
            </Button>
          </Link>
          <Link to="/login">
            <Button type="button" variant="secondary" size="sm">
              Demo-вход
            </Button>
          </Link>
        </div>
      </header>

      <div className={styles.shell}>
        <div className={styles.hero}>
          <p className={styles.heroEyebrow}>FSP Brandbook · JetBrains Mono · Golos Text</p>
          <h1 className={styles.heroTitle}>
            Дизайн-система
            <br />
            FSP Talent
          </h1>
          <p className={styles.heroLead}>
            Единые токены, shared UI и domain-компоненты для кабинетов кандидата, работодателя и
            администратора. Фирменный фиолетовый #402FFF, без второй палитры.
          </p>
          <div className={styles.heroStats}>
            <div className={styles.stat}>
              <span className={styles.statValue}>
                {BRAND_COLORS.length + PRIMARY_SCALE.length + SURFACE_COLORS.length + SEMANTIC_COLORS.length}
              </span>
              <span className={styles.statLabel}>color tokens</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>16</span>
              <span className={styles.statLabel}>shared UI</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>16</span>
              <span className={styles.statLabel}>domain UI</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>4px</span>
              <span className={styles.statLabel}>grid step</span>
            </div>
          </div>
        </div>

        <nav className={styles.sideNav} aria-label="Разделы UI Kit">
          <p className={styles.sideNavTitle}>Навигация</p>
          {NAV.map((item) => (
            <a
              key={item.id}
              href={`#${item.id}`}
              aria-current={activeNav === item.id ? 'true' : undefined}
              onClick={(e) => {
                e.preventDefault();
                document.getElementById(item.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
              }}
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className={styles.main}>
          <nav className={styles.mobileNav} aria-label="Разделы UI Kit">
            {NAV.map((item) => (
              <a key={item.id} href={`#${item.id}`}>
                {item.label}
              </a>
            ))}
          </nav>

          <Section id="foundations" title="Foundations" hint="src/styles/global.css · только CSS variables">
            <Canvas label="Brand · ФСП brandbook">
              <SwatchGrid items={BRAND_COLORS} />
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="Primary scale">
              <SwatchGrid items={PRIMARY_SCALE} />
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="Surfaces · text · borders">
              <SwatchGrid items={SURFACE_COLORS} />
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="Semantic">
              <SwatchGrid items={SEMANTIC_COLORS} />
            </Canvas>
            <div className={styles.gap} />
            <div className={styles.grid2}>
              <Canvas label="Spacing · 4px grid">
                <div className={styles.spaceRow}>
                  {SPACES.map((s) => (
                    <div key={s.token} className={styles.spaceBox}>
                      <div className={styles.spaceChip} style={{ width: s.px, height: s.px }} />
                      <span className={styles.typeMeta}>
                        {s.token}
                        <br />
                        {s.px}px
                      </span>
                    </div>
                  ))}
                </div>
              </Canvas>
              <Canvas label="Radius">
                <div className={styles.radiusDemo}>
                  {RADII.map((r) => (
                    <div key={r.token} className={styles.radiusItem}>
                      <div className={styles.radiusBox} style={{ borderRadius: r.css }} />
                      <span className={styles.typeMeta}>
                        {r.value}
                        <br />
                        {r.token}
                      </span>
                    </div>
                  ))}
                </div>
              </Canvas>
            </div>
            <div className={styles.gap} />
            <Canvas label="Shadows">
              <div className={styles.shadowDemo}>
                <div className={styles.shadowCard} style={{ boxShadow: 'var(--shadow-card)' }}>
                  --shadow-card
                </div>
                <div className={styles.shadowCard} style={{ boxShadow: 'var(--shadow-card-hover)' }}>
                  --shadow-card-hover
                </div>
                <div className={styles.shadowCard} style={{ boxShadow: 'var(--shadow-dropdown)' }}>
                  --shadow-dropdown
                </div>
              </div>
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="Import">
              <pre className={styles.importBox}>{`import { Button, Input, Badge, Switch } from '@/shared/ui';
import { MatchScore } from '@/entities/ui/MatchScore';
/* tokens: var(--brand-primary) — never hardcode HEX */`}</pre>
            </Canvas>
          </Section>

          <Section id="typography" title="Typography" hint="JetBrains Mono · H1–H3 / KPI · Golos Text · UI body">
            <Canvas label="Type scale">
              <div className={styles.typeSample}>
                <div className={styles.typeRow}>
                  <p className={styles.typeOverline}>Overline · 11 / 600</p>
                  <p className={styles.typeH1}>H1 · 32 / 700</p>
                  <p className={styles.typeMeta}>JetBrains Mono · line-height 40</p>
                </div>
              </div>
              <div className={styles.typeSample}>
                <p className={styles.typeH2}>H2 · 26 / 700</p>
                <p className={styles.typeH3}>H3 · 22 / 600</p>
                <p className={styles.typeH4}>H4 · 18 / 600</p>
              </div>
              <div className={styles.typeSample}>
                <p className={styles.typeBodyLg}>Body Large · 16 / 400 — описания и лиды.</p>
                <p className={styles.typeBody}>Body · 14 / 400 — основной UI-текст, формы, таблицы.</p>
                <p className={styles.typeSmall}>Body Small · 13 / 400 — вторичные описания.</p>
                <p className={styles.typeCaption}>Caption · 12 / 400 — мета, ошибки, бейджи.</p>
              </div>
              <div className={styles.typeSample}>
                <p className={styles.typeKpi}>87%</p>
                <p className={styles.typeMeta}>KPI · tabular-nums · JetBrains Mono</p>
              </div>
            </Canvas>
          </Section>

          <Section id="buttons" title="Buttons" hint="shared/ui/Button · primary / secondary / outline / ghost / danger">
            <Canvas label="Variants">
              <div className={styles.row}>
                <Button type="button">Primary</Button>
                <Button type="button" variant="secondary">
                  Secondary
                </Button>
                <Button type="button" variant="outline">
                  Outline
                </Button>
                <Button type="button" variant="ghost">
                  Ghost
                </Button>
                <Button type="button" variant="danger">
                  Destructive
                </Button>
              </div>
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="Sizes · sm 36 · md 44 · lg 48">
              <div className={styles.row}>
                <Button type="button" size="sm">
                  Small
                </Button>
                <Button type="button" size="md">
                  Medium
                </Button>
                <Button type="button" size="lg">
                  Large
                </Button>
                <Button type="button" disabled>
                  Disabled
                </Button>
              </div>
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="With icons · Lucide 20px">
              <div className={styles.row}>
                <Button type="button">
                  <Search size={20} strokeWidth={1.75} />
                  Найти кандидатов
                </Button>
                <Button type="button" variant="secondary">
                  <Users size={20} strokeWidth={1.75} />
                  Shortlist
                </Button>
              </div>
            </Canvas>
          </Section>

          <Section id="forms" title="Forms" hint="Input · Select · Textarea · Checkbox · Radio · Switch">
            <div className={styles.grid2}>
              <Canvas label="Controls">
                <div className={styles.stack}>
                  <Input
                    label="Email"
                    name="kit-email"
                    placeholder="candidate@demo.ru"
                    defaultValue="candidate@demo.ru"
                  />
                  <Input label="С ошибкой" name="kit-error" error="Укажите корректный email" />
                  <Select
                    label="Роль"
                    name="kit-role"
                    options={[
                      { value: 'candidate', label: 'Кандидат' },
                      { value: 'employer', label: 'Работодатель' },
                    ]}
                  />
                  <Textarea
                    label="О себе"
                    name="kit-about"
                    rows={3}
                    defaultValue="Frontend, React, дизайн-системы."
                  />
                </div>
              </Canvas>
              <Canvas label="Choice controls">
                <div className={styles.stack}>
                  <Checkbox
                    label="Открыт к офферам"
                    name="kit-ready"
                    checked={checked}
                    onChange={(e) => setChecked(e.target.checked)}
                  />
                  <Switch
                    label="Уведомления о новых вакансиях"
                    name="kit-switch"
                    checked={switchOn}
                    onChange={(e) => setSwitchOn(e.target.checked)}
                  />
                  <div className={styles.stack} style={{ gap: 8 }}>
                    <Radio
                      label="Удалённо"
                      name="kit-format"
                      value="remote"
                      checked={radioVal === 'remote'}
                      onChange={() => setRadioVal('remote')}
                    />
                    <Radio
                      label="Гибрид"
                      name="kit-format"
                      value="hybrid"
                      checked={radioVal === 'hybrid'}
                      onChange={() => setRadioVal('hybrid')}
                    />
                    <Radio
                      label="Офис"
                      name="kit-format"
                      value="office"
                      checked={radioVal === 'office'}
                      onChange={() => setRadioVal('office')}
                    />
                  </div>
                  <Tabs
                    tabs={[
                      { id: 'overview', label: 'Обзор' },
                      { id: 'fsp', label: 'ФСП' },
                      { id: 'tests', label: 'Тесты' },
                    ]}
                    value={tab}
                    onChange={setTab}
                  />
                  <p className={styles.typeCaption}>
                    Активная вкладка: <strong>{tab}</strong>
                  </p>
                </div>
              </Canvas>
            </div>
          </Section>

          <Section
            id="feedback"
            title="Feedback & states"
            hint="loading · empty · error · progress · modal · toast"
          >
            <div className={styles.stateGrid}>
              <Canvas label="Loading">
                <Loader label="Загрузка Talent Pool…" />
                <div className={styles.stack} style={{ marginTop: 16 }}>
                  <Skeleton height={18} width="70%" />
                  <Skeleton height={14} />
                  <Skeleton height={14} width="85%" />
                </div>
              </Canvas>
              <Canvas label="Empty">
                <EmptyState
                  title="Пока нет входящих предложений"
                  description="Когда работодатели отправят приглашения, они появятся здесь."
                  action={
                    <Button type="button" variant="secondary">
                      Открыть профиль
                    </Button>
                  }
                />
              </Canvas>
              <Canvas label="Error">
                <ErrorState
                  title="Не удалось загрузить"
                  description="Backend временно недоступен."
                  onRetry={() => undefined}
                />
              </Canvas>
              <Canvas label="Progress + Modal">
                <p className={styles.canvasLabel} style={{ marginBottom: 8 }}>
                  Profile completeness 72%
                </p>
                <ProgressBar value={72} />
                <div style={{ marginTop: 16 }}>
                  <Button type="button" onClick={() => setModalOpen(true)}>
                    Открыть Modal
                  </Button>
                </div>
              </Canvas>
            </div>
            <div className={styles.gap} />
            <Canvas label="Toast patterns">
              <div className={styles.toastStack}>
                <div className={`${styles.toast} ${styles.toastSuccess}`}>
                  <CheckCircle2 size={20} strokeWidth={1.75} />
                  Профиль сохранён
                </div>
                <div className={`${styles.toast} ${styles.toastInfo}`}>
                  <Info size={20} strokeWidth={1.75} />
                  Найдено 24 кандидата
                </div>
                <div className={`${styles.toast} ${styles.toastWarn}`}>
                  <AlertTriangle size={20} strokeWidth={1.75} />
                  Срок оффера истекает через 2 дня
                </div>
                <div className={`${styles.toast} ${styles.toastError}`}>
                  <AlertCircle size={20} strokeWidth={1.75} />
                  Ошибка API — повторите позже
                </div>
              </div>
            </Canvas>
            <Modal open={modalOpen} title="Отправить оффер" onClose={() => setModalOpen(false)}>
              <p className={styles.typeBody}>
                Modal 560px · radius 20 · overlay rgba(27,28,33,0.45). Escape / backdrop закрывают.
              </p>
              <div className={styles.row}>
                <Button type="button" onClick={() => setModalOpen(false)}>
                  Понятно
                </Button>
                <Button type="button" variant="ghost" onClick={() => setModalOpen(false)}>
                  Отмена
                </Button>
              </div>
            </Modal>
          </Section>

          <Section id="badges" title="Badges & skill chips" hint="Статусы + skill chips · не путать Verified без источника">
            <Canvas label="Badge tones">
              <div className={styles.row}>
                <Badge>Заявлено кандидатом</Badge>
                <Badge tone="accent">Оффер просмотрен</Badge>
                <Badge tone="success">Подтверждён тестом</Badge>
                <Badge tone="warn">Ожидает проверки</Badge>
                <Badge tone="danger">Оффер отклонён</Badge>
                <Badge tone="fsp">Демо-интеграция ФСП</Badge>
              </div>
            </Canvas>
            <div className={styles.gap} />
            <div className={styles.grid2}>
              <Canvas label="Domain badges">
                <div className={styles.row}>
                  <GradeBadge grade="middle" />
                  <GradeBadge grade="senior" />
                  <FSPVerificationBadge />
                  <FSPVerificationBadge label="FSP Verified" />
                </div>
                <div className={styles.row} style={{ marginTop: 14 }}>
                  {['Python', 'React', 'TypeScript', 'FastAPI', 'PostgreSQL'].map((skill) => (
                    <SkillBadge key={skill} skill={skill} />
                  ))}
                </div>
              </Canvas>
              <Canvas label="SalaryRange">
                <p className={styles.typeKpi} style={{ fontSize: 22, lineHeight: '30px' }}>
                  <SalaryRange from={250000} to={320000} currency="RUB" />
                </p>
                <p className={styles.typeMeta}>formatters · не считать бизнес-логику на клиенте</p>
              </Canvas>
            </div>
            <div className={styles.gap} />
            <Canvas label="Icons · Lucide only">
              <div className={styles.iconRow}>
                <div className={styles.iconItem}>
                  <Search size={16} strokeWidth={1.75} />
                  16
                </div>
                <div className={styles.iconItem}>
                  <Bell size={20} strokeWidth={1.75} />
                  20
                </div>
                <div className={`${styles.iconItem} ${styles.iconActive}`}>
                  <LayoutDashboard size={24} strokeWidth={1.75} />
                  24 active
                </div>
                <div className={styles.iconItem}>
                  <Briefcase size={28} strokeWidth={1.75} />
                  28
                </div>
              </div>
            </Canvas>
          </Section>

          <Section id="layout" title="Layout chrome" hint="Sidebar 244 · Topbar 72 · Bento 12-col · gap 16">
            <Canvas label="App shell preview">
              <div className={styles.chromeDemo}>
                <aside className={styles.chromeSidebar}>
                  <div className={styles.chromeNavItem}>FSP Talent</div>
                  <div className={`${styles.chromeNavItem} ${styles.chromeNavItemActive}`}>Обзор</div>
                  <div className={styles.chromeNavItem}>Профиль</div>
                  <div className={styles.chromeNavItem}>Talent Pool</div>
                  <div className={styles.chromeNavItem}>Офферы</div>
                </aside>
                <div className={styles.chromeMain}>
                  <div className={styles.chromeTopbar}>
                    <Bell size={20} strokeWidth={1.75} color="var(--text-secondary)" />
                    <div className={styles.chromeNavItem} style={{ minHeight: 0, padding: 0 }}>
                      А. Иванов · Кандидат
                    </div>
                  </div>
                  <div className={styles.chromeBody}>
                    <div className={styles.chromeCard}>
                      <p className={styles.typeH4} style={{ margin: 0 }}>
                        Контент страницы
                      </p>
                      <p className={styles.typeCaption}>page padding 24 · content max 1600</p>
                    </div>
                  </div>
                </div>
              </div>
            </Canvas>
            <div className={styles.gap} />
            <Canvas label="Bento cards">
              <div className={styles.bentoGrid}>
                <Card variant="hero" className={styles.bento6}>
                  <p className={styles.typeOverline}>Hero card</p>
                  <h3 style={{ margin: '8px 0' }}>Цифровой карьерный паспорт</h3>
                  <p className={styles.typeSmall} style={{ margin: 0 }}>
                    Radius 20 · padding 28 · слабый primary gradient · ≤2 CTA
                  </p>
                  <div className={styles.row} style={{ marginTop: 16 }}>
                    <Button type="button" size="sm">
                      Пройти тест
                    </Button>
                    <Button type="button" variant="ghost" size="sm">
                      Редактировать
                    </Button>
                  </div>
                </Card>
                <Card className={styles.bento3}>
                  <p className={styles.metricValue}>92</p>
                  <p className={styles.metricLabel}>Match Score</p>
                </Card>
                <Card className={styles.bento3}>
                  <p className={styles.metricValue}>Middle</p>
                  <p className={styles.metricLabel}>Подтверждённый грейд</p>
                </Card>
                <Card variant="compact" className={styles.bento4}>
                  <p className={styles.typeH4} style={{ margin: 0 }}>
                    Compact
                  </p>
                  <p className={styles.typeCaption}>padding 16 · radius 12</p>
                </Card>
                <Card className={styles.bento4}>
                  <p className={styles.typeH4} style={{ margin: 0 }}>
                    Bento default
                  </p>
                  <p className={styles.typeCaption}>padding 24 · radius 16 · shadow-card</p>
                </Card>
                <Card className={styles.bento4} to="/ui-kit#layout">
                  <p className={styles.typeH4} style={{ margin: 0 }}>
                    Interactive
                  </p>
                  <p className={styles.typeCaption}>hover → border-hover + shadow-card-hover</p>
                </Card>
              </div>
            </Canvas>
          </Section>

          <Section id="tables" title="Tables" hint="Header #F7F7FA · row 56 · hover #F7F6FF · selected primary-50">
            <Canvas label="Admin / invitations pattern">
              <div className={styles.tableWrap}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th>Кандидат</th>
                      <th>Грейд</th>
                      <th>Статус</th>
                      <th>Match</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr data-selected="true">
                      <td>Алина Котова</td>
                      <td>Middle</td>
                      <td>
                        <Badge tone="success">Подтверждён тестом</Badge>
                      </td>
                      <td>92%</td>
                    </tr>
                    <tr>
                      <td>Игорь Семёнов</td>
                      <td>Junior</td>
                      <td>
                        <Badge tone="warn">Ожидает проверки</Badge>
                      </td>
                      <td>71%</td>
                    </tr>
                    <tr>
                      <td>Мария Орлова</td>
                      <td>—</td>
                      <td>
                        <Badge>Не подтверждён</Badge>
                      </td>
                      <td>54%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Canvas>
          </Section>

          <Section id="domain" title="Domain cards" hint="entities/ui · props = DTO, без fetch">
            <div className={styles.grid2}>
              <Canvas label="CandidateCard">
                <CandidateCard candidate={talentItem} to="/ui-kit#domain" />
              </Canvas>
              <Canvas label="VacancyCard">
                <VacancyCard vacancy={vacancies[0]} to="/ui-kit#domain" />
              </Canvas>
              <Canvas label="OfferCard">
                <OfferCard offer={offers[0]} to="/ui-kit#domain" />
              </Canvas>
              <Canvas label="FSPAchievementCard">
                {achievement ? (
                  <FSPAchievementCard achievement={achievement} />
                ) : (
                  <EmptyState title="Нет FSP demo" />
                )}
              </Canvas>
            </div>
            <div className={styles.gap} />
            <Canvas label="CandidateProfileView · employer mode">
              <CandidateProfileView
                profile={profile}
                achievements={fspByCandidate[profile.id] ?? []}
                match={match}
                mode="employer"
              />
            </Canvas>
          </Section>

          <Section id="match" title="Match Score & Skill Radar" hint="Только отображение DTO с backend">
            <div className={styles.grid2}>
              <Canvas label="MatchScore">
                <MatchScore match={match} />
              </Canvas>
              <Canvas label="SkillRadar">
                <SkillRadar radar={radar} size={260} />
              </Canvas>
            </div>
          </Section>

          <Section id="testing" title="Testing" hint="TestQuestion · TestResult · ProgressBar">
            <div className={styles.grid2}>
              <Canvas label="TestQuestionView">
                {question ? (
                  <TestQuestionView
                    question={question}
                    selected={selectedOption}
                    onSelect={setSelectedOption}
                    onNext={() => undefined}
                    isLast={false}
                  />
                ) : null}
              </Canvas>
              <Canvas label="TestResultView">
                <TestResultView
                  result={{
                    sessionId: 'demo-session',
                    score: 82,
                    maxScore: 100,
                    gradeConfirmed: true,
                    claimedGrade: 'middle',
                    completedAt: '2026-09-12T10:00:00.000Z',
                    isRetest: false,
                  }}
                />
              </Canvas>
            </div>
          </Section>

          <Section id="offer" title="Offer form" hint="react-hook-form + zod · entities/ui/OfferForm">
            <Canvas label="OfferForm">
              <OfferForm
                vacancies={vacancies.filter((v) => v.status === 'active')}
                candidateId={profile.id}
                onSubmit={async () => undefined}
              />
            </Canvas>
          </Section>

          <Section id="landing" title="Landing surface" hint="LandingPage.module.css · shared FSP tokens">
            <div className={styles.landingStrip}>
              <div className={styles.landingLight}>
                <div>
                  <p className={styles.landingBrand}>FSP Talent</p>
                  <p style={{ margin: '8px 0 0', opacity: 0.75, fontSize: 13 }}>
                    Page #F7F7FA · Primary #402FFF · JetBrains Mono
                  </p>
                </div>
                <div className={styles.landingCtas}>
                  <span className={styles.lBtnPrimary}>Начать</span>
                  <span className={styles.lBtnSecondary}>Demo-вход</span>
                </div>
              </div>
              <div className={styles.landingHero}>
                <div>
                  <p className={styles.landingBrand}>FSP Talent</p>
                  <p style={{ margin: '8px 0 0', opacity: 0.75, fontSize: 13 }}>
                    Full-bleed hero · brand first · no cards in first viewport
                  </p>
                </div>
                <div className={styles.landingCtas}>
                  <span className={styles.lBtnPrimary}>Начать</span>
                  <span className={styles.lBtnSecondaryGhost}>Demo-вход</span>
                </div>
              </div>
            </div>
            <p className={styles.footerNote}>
              Landing: sticky topbar 72px, bento 16px, buttons 12px / 44px. Красный #EC1D35 — только
              фирменные акценты и destructive, не primary CTA.
            </p>
          </Section>

          <Section id="rules" title="Rules" hint="Не ломай границы продукта">
            <div className={styles.principles}>
              {[
                ['Backend owns truth', 'Match Score, test scores, FSP, contacts — только DTO.'],
                ['No false claims', '«не указан в профиле» ≠ «не умеет».'],
                ['FSP ≠ self-reported', 'FSPVerificationBadge только на данных ФСП.'],
                ['Tokens only', 'HEX в компонентах запрещён — только CSS variables.'],
                ['One system', 'Все три кабинета на одной палитре и компонентах.'],
                ['6 states', 'loading · success · empty · error · disabled · action success.'],
              ].map(([title, text], i) => (
                <div key={title} className={styles.principle}>
                  <span className={styles.principleNum}>0{i + 1}</span>
                  <div>
                    <strong>{title}</strong>
                    <span>{text}</span>
                  </div>
                </div>
              ))}
            </div>
            <p className={styles.footerNote}>
              Спека: <code className={styles.codeChip}>frontend/UI_KIT.md</code> · brandbook:{' '}
              <a href="https://fsp-russia.ru/press/brandbook/" target="_blank" rel="noreferrer">
                fsp-russia.ru/press/brandbook
              </a>{' '}
              · этот экран — visual source of truth.
            </p>
          </Section>
        </div>
      </div>
    </div>
  );
}
