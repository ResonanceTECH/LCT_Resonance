import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { Loader } from '@/shared/ui';
import {
  landingCta,
  landingDock,
  landingFeatures,
  landingFooter,
  landingHero,
  landingHowItWorks,
  landingRoles,
  type FeaturesMode,
} from '@/pages/landing/content';
import styles from './LandingPage.module.css';

const SECTION_IDS = landingDock.map((item) => item.id);

function scrollToHash(href: string) {
  const id = href.startsWith('#') ? href.slice(1) : href;
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function getActiveSectionId(ids: string[]): string | null {
  const offset = 120;
  let active: string | null = null;
  for (const id of ids) {
    const el = document.getElementById(id);
    if (!el) continue;
    if (el.getBoundingClientRect().top - offset <= 0) active = id;
  }
  return active;
}

function MatchRing({ value, size = 44 }: { value: number; size?: number }) {
  const r = 16;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <svg className={styles.ring} style={{ width: size, height: size }} viewBox="0 0 40 40" aria-hidden>
      <circle cx="20" cy="20" r={r} className={styles.ringTrack} />
      <circle
        cx="20"
        cy="20"
        r={r}
        className={styles.ringValue}
        strokeDasharray={c}
        strokeDashoffset={offset}
      />
    </svg>
  );
}

const CANDIDATE_NAV = [
  'Обзор',
  'Профиль',
  'ФСП',
  'Тесты',
  'Предложения',
  'Вакансии',
] as const;

const EMPLOYER_NAV = [
  'Обзор',
  'Пул кандидатов',
  'Вакансии',
  'Избранное',
  'Сравнение',
  'Предложения',
] as const;

const CANDIDATE_NAV_BY_STEP: Record<string, number> = {
  profile: 1,
  fsp: 2,
  tests: 3,
  offers: 4,
};

const EMPLOYER_NAV_BY_STEP: Record<string, number> = {
  vacancy: 2,
  pool: 1,
  compare: 4,
  offer: 5,
};

const DEMO_CANDIDATES = [
  {
    initials: 'АК',
    name: 'Алина К.',
    role: 'Бэкенд · средний',
    match: 92,
    skills: ['Go', 'PostgreSQL', 'Docker'],
    badges: ['ФСП', 'Тест'],
    reason: 'Совпал стек · есть достижения ФСП',
  },
  {
    initials: 'МР',
    name: 'Максим Р.',
    role: 'Бэкенд · старший',
    match: 84,
    skills: ['Python', 'FastAPI', 'Redis'],
    badges: ['Тест'],
    reason: 'Уровень подтверждён тестом',
  },
  {
    initials: 'ИС',
    name: 'Игорь С.',
    role: 'Фулстек · средний',
    match: 77,
    skills: ['TypeScript', 'React', 'Go'],
    badges: ['Заявлено'],
    reason: 'Частичное совпадение по стеку',
  },
] as const;

function SkillChips({ skills }: { skills: readonly string[] }) {
  return (
    <div className={styles.uiSkills}>
      {skills.map((s) => (
        <span key={s} className={styles.uiSkill}>
          {s}
        </span>
      ))}
    </div>
  );
}

function PreviewPageHead({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: string;
}) {
  return (
    <div className={styles.uiPageHead}>
      <div>
        <h3 className={styles.uiPageTitle}>{title}</h3>
        <p className={styles.uiPageSub}>{subtitle}</p>
      </div>
      {action ? <span className={styles.uiBtnPrimary}>{action}</span> : null}
    </div>
  );
}

function CandidatePreviewBody({ stepId }: { stepId: string }) {
  if (stepId === 'fsp') {
    return (
      <>
        <PreviewPageHead title="Достижения ФСП" subtitle="Подтверждённые факты отдельно от заявленных навыков" />
        <div className={styles.uiCardList}>
          {[
            { title: 'Олимпиада ФСП', meta: 'Алгоритмы · 2025 · топ-10%', tone: 'ok' as const },
            { title: 'Рейтинг дисциплины', meta: 'Спортивное программирование · активен', tone: 'ok' as const },
            { title: 'Заявленный Kafka', meta: 'Не из реестра ФСП', tone: 'muted' as const },
          ].map((row) => (
            <div key={row.title} className={styles.uiRowCard}>
              <div>
                <p className={styles.uiRowTitle}>{row.title}</p>
                <p className={styles.uiRowMeta}>{row.meta}</p>
              </div>
              <span className={row.tone === 'ok' ? styles.uiBadgeOk : styles.uiBadgeMute}>
                {row.tone === 'ok' ? 'ФСП' : 'Заявлено'}
              </span>
            </div>
          ))}
        </div>
      </>
    );
  }

  if (stepId === 'tests') {
    return (
      <>
        <PreviewPageHead title="Тестирование" subtitle="Результат влияет на оценку соответствия" action="Начать тест" />
        <div className={styles.uiSplit}>
          <div className={styles.uiPanel}>
            <div className={styles.uiMatchHero}>
              <MatchRing value={82} size={64} />
              <div>
                <p className={styles.uiMatchValue}>82 / 100</p>
                <p className={styles.uiRowMeta}>Бэкенд · средний · подтверждён</p>
              </div>
            </div>
            <div className={styles.uiProgressTrack}>
              <span style={{ width: '82%' }} />
            </div>
          </div>
          <div className={styles.uiPanel}>
            <p className={styles.uiPanelLabel}>Навыки по источнику</p>
            <ul className={styles.uiPlainList}>
              <li>
                <span>Go</span>
                <span className={styles.uiBadgeOk}>тест</span>
              </li>
              <li>
                <span>PostgreSQL</span>
                <span className={styles.uiBadgeOk}>тест</span>
              </li>
              <li>
                <span>Kafka</span>
                <span className={styles.uiBadgeMute}>заявлено</span>
              </li>
            </ul>
          </div>
        </div>
      </>
    );
  }

  if (stepId === 'offers') {
    return (
      <>
        <PreviewPageHead title="Входящие предложения" subtitle="Контакты скрыты до согласия" />
        <div className={styles.uiCardList}>
          {[
            { company: 'Компания А', role: 'Старший бэкенд', pay: '280–320 тыс ₽', status: 'Новое' },
            { company: 'Компания Б', role: 'Инженер данных', pay: '250–290 тыс ₽', status: 'Просмотрено' },
          ].map((o) => (
            <div key={o.company} className={styles.uiRowCard}>
              <div>
                <p className={styles.uiRowTitle}>
                  {o.company} · {o.role}
                </p>
                <p className={styles.uiRowMeta}>
                  {o.pay} · удалённо · контакты закрыты
                </p>
              </div>
              <span className={styles.uiBadgeAccent}>{o.status}</span>
            </div>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <PreviewPageHead
        title="Кабинет кандидата"
        subtitle="Сводка по профилю, предложениям и заполненности"
        action="Редактировать"
      />
      <div className={styles.uiStats}>
        {[
          ['Просмотры', '128'],
          ['Предложения', '2'],
          ['Принято', '0'],
          ['Заполненность', '72%'],
        ].map(([label, value]) => (
          <div key={label} className={styles.uiStat}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className={styles.uiPanel}>
        <div className={styles.uiPerson}>
          <span className={styles.uiAvatar}>АК</span>
          <div>
            <p className={styles.uiRowTitle}>Алина К.</p>
            <p className={styles.uiRowMeta}>Инженер бэкенда · средний · гибрид</p>
          </div>
          <span className={styles.uiBadgeMute}>ФСП не синхр.</span>
        </div>
        <SkillChips skills={['Go', 'PostgreSQL', 'Docker', 'Kafka']} />
        <div className={styles.uiProgressTrack}>
          <span style={{ width: '72%' }} />
        </div>
        <p className={styles.uiRowMeta}>Заполненность профиля 72%</p>
      </div>
    </>
  );
}

function EmployerPreviewBody({ stepId }: { stepId: string }) {
  if (stepId === 'vacancy') {
    return (
      <>
        <PreviewPageHead title="Новая вакансия" subtitle="Стек и вилка — часть сигнала" action="Опубликовать" />
        <div className={styles.uiForm}>
          {[
            ['Должность', 'Старший инженер бэкенда'],
            ['Уровень', 'Старший'],
            ['Вилка', '280–350 тыс ₽'],
            ['Формат', 'Удалённо'],
            ['Стек', 'Go, PostgreSQL, Kafka'],
          ].map(([label, value]) => (
            <label key={label} className={styles.uiField}>
              <span>{label}</span>
              <div>{value}</div>
            </label>
          ))}
        </div>
      </>
    );
  }

  if (stepId === 'compare') {
    return (
      <>
        <PreviewPageHead title="Сравнение" subtitle="До 4 кандидатов рядом" action="Отправить предложение" />
        <div className={styles.uiCompare}>
          {DEMO_CANDIDATES.slice(0, 2).map((c) => (
            <div key={c.name} className={styles.uiCompareCol}>
              <div className={styles.uiPerson}>
                <span className={styles.uiAvatar}>{c.initials}</span>
                <div>
                  <p className={styles.uiRowTitle}>{c.name}</p>
                  <p className={styles.uiRowMeta}>{c.role}</p>
                </div>
              </div>
              <div className={styles.uiMatchHero}>
                <MatchRing value={c.match} />
                <p className={styles.uiMatchValue}>{c.match}%</p>
              </div>
              <SkillChips skills={c.skills} />
              <div className={styles.uiBadgeRow}>
                {c.badges.map((b) => (
                  <span key={b} className={b === 'ФСП' ? styles.uiBadgeOk : styles.uiBadgeAccent}>
                    {b}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </>
    );
  }

  if (stepId === 'offer') {
    return (
      <>
        <PreviewPageHead title="Новое предложение" subtitle="Алина К. · соответствие 92%" action="Отправить" />
        <div className={styles.uiForm}>
          {[
            ['Кандидат', 'Алина К. · бэкенд · средний'],
            ['Вакансия', 'Старший инженер бэкенда'],
            ['Вилка', '300 тыс ₽'],
            ['Формат', 'Удалённо · полная занятость'],
            ['Контакты', 'Скрыты до согласия'],
          ].map(([label, value]) => (
            <label key={label} className={styles.uiField}>
              <span>{label}</span>
              <div>{value}</div>
            </label>
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <PreviewPageHead
        title="Пул кандидатов"
        subtitle="Оценка соответствия по вакансии «Старший бэкенд»"
        action="Сравнить (2)"
      />
      <div className={styles.uiFilters}>
        <span className={styles.uiFilterActive}>Вакансия: старший бэкенд</span>
        <span className={styles.uiFilter}>Уровень</span>
        <span className={styles.uiFilter}>ФСП</span>
        <span className={styles.uiFilter}>Формат</span>
        <span className={styles.uiFilter}>Стек</span>
      </div>
      <div className={styles.uiCardList}>
        {DEMO_CANDIDATES.map((c) => (
          <article key={c.name} className={styles.uiCandidate}>
            <div className={styles.uiCandidateTop}>
              <div className={styles.uiPerson}>
                <span className={styles.uiAvatar}>{c.initials}</span>
                <div>
                  <p className={styles.uiRowTitle}>{c.name}</p>
                  <p className={styles.uiRowMeta}>{c.role}</p>
                </div>
              </div>
              <div className={styles.uiMatchPill}>
                <MatchRing value={c.match} size={36} />
                <div>
                  <strong>{c.match}%</strong>
                  <span>соответствие</span>
                </div>
              </div>
            </div>
            <SkillChips skills={c.skills} />
            <div className={styles.uiCandidateFoot}>
              <div className={styles.uiBadgeRow}>
                {c.badges.map((b) => (
                  <span key={b} className={b === 'ФСП' ? styles.uiBadgeOk : styles.uiBadgeAccent}>
                    {b}
                  </span>
                ))}
              </div>
              <p className={styles.uiRowMeta}>{c.reason}</p>
            </div>
          </article>
        ))}
      </div>
    </>
  );
}

function ProductPreview({
  mode = 'employer',
  stepId,
  compact = false,
}: {
  mode?: FeaturesMode;
  stepId?: string;
  compact?: boolean;
}) {
  const isCandidate = mode === 'candidate';
  const nav = isCandidate ? CANDIDATE_NAV : EMPLOYER_NAV;
  const activeNav =
    (isCandidate ? CANDIDATE_NAV_BY_STEP[stepId ?? 'profile'] : EMPLOYER_NAV_BY_STEP[stepId ?? 'pool']) ?? 0;
  const resolvedStep = stepId ?? (isCandidate ? 'profile' : 'pool');
  const userName = isCandidate ? 'Алина К.' : 'ООО «Сигнал»';
  const userRole = isCandidate ? 'Кандидат' : 'Работодатель';
  const userInitials = isCandidate ? 'АК' : 'СР';

  return (
    <div
      className={`${styles.preview} ${compact ? styles.previewCompact : ''}`}
      data-mode={mode}
      aria-hidden
    >
      <aside className={styles.previewAside}>
        <img src="/fsp-logo-dark.svg" alt="" className={styles.previewLogo} width={120} height={40} />
        <nav className={styles.previewNav}>
          {nav.map((label, i) => (
            <div key={label} className={i === activeNav ? styles.previewNavActive : styles.previewNavItem}>
              {label}
            </div>
          ))}
        </nav>
      </aside>

      <div className={styles.previewChrome}>
        <header className={styles.previewTopbar}>
          <div className={styles.previewSearch}>Поиск по стеку, уровню, ФСП…</div>
          <span className={styles.previewBell} />
          <div className={styles.previewUser}>
            <span className={styles.uiAvatar}>{userInitials}</span>
            <div>
              <strong>{userName}</strong>
              <span>{userRole}</span>
            </div>
          </div>
        </header>
        <div className={styles.previewMain} key={`${mode}-${resolvedStep}`}>
          {isCandidate ? (
            <CandidatePreviewBody stepId={resolvedStep} />
          ) : (
            <EmployerPreviewBody stepId={resolvedStep} />
          )}
        </div>
      </div>
    </div>
  );
}

function LandingHeader() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const menuId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => {
        setScrolled(window.scrollY > 8);
        setActiveId(getActiveSectionId(SECTION_IDS));
      });
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setMenuOpen(false);
        toggleRef.current?.focus();
      }
    };
    const onPointer = (e: MouseEvent) => {
      const t = e.target as Node;
      if (panelRef.current?.contains(t) || toggleRef.current?.contains(t)) return;
      setMenuOpen(false);
    };
    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onPointer);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onPointer);
      document.body.style.overflow = '';
    };
  }, [menuOpen]);

  const solid = scrolled || menuOpen;

  return (
    <header className={`${styles.header} ${solid ? styles.headerSolid : ''}`}>
      <div className={styles.headerInner}>
        <Link to="/" className={styles.logo} aria-label={`${landingHero.brand} — ${landingHero.brandTagline}`}>
          <img
            src={solid ? '/fsp-logo-dark.svg' : '/fsp-logo.svg'}
            alt=""
            className={styles.logoImg}
            width={138}
            height={47}
            decoding="async"
          />
        </Link>

        <nav className={styles.headerNav} aria-label="Разделы лендинга">
          {landingDock.map((item) => (
            <a
              key={item.id}
              href={item.href}
              className={activeId === item.id ? styles.headerNavActive : styles.headerNavLink}
              onClick={(e) => {
                e.preventDefault();
                scrollToHash(item.href);
              }}
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className={styles.headerActions}>
          <div className={styles.headerAuth}>
            <Link className={styles.btnOutline} to="/login">
              Войти
            </Link>
            <Link className={styles.btnPrimary} to="/register">
              Регистрация
            </Link>
          </div>
          <button
            ref={toggleRef}
            type="button"
            className={styles.menuBtn}
            aria-expanded={menuOpen}
            aria-controls={menuId}
            aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
            onClick={() => setMenuOpen((v) => !v)}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden>
              {menuOpen ? (
                <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              ) : (
                <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {menuOpen ? (
        <div
          id={menuId}
          ref={panelRef}
          className={styles.mobileMenu}
          role="dialog"
          aria-modal="true"
          aria-label="Мобильное меню"
        >
          <nav className={styles.mobileNav} aria-label="Разделы">
            {landingDock.map((item) => (
              <a
                key={item.id}
                href={item.href}
                className={activeId === item.id ? styles.mobileNavActive : undefined}
                onClick={(e) => {
                  e.preventDefault();
                  setMenuOpen(false);
                  scrollToHash(item.href);
                }}
              >
                {item.label}
              </a>
            ))}
          </nav>
          <div className={styles.mobileAuth}>
            <Link className={styles.btnOutline} to="/login" onClick={() => setMenuOpen(false)}>
              Войти
            </Link>
            <Link className={styles.btnPrimary} to="/register" onClick={() => setMenuOpen(false)}>
              Регистрация
            </Link>
          </div>
        </div>
      ) : null}
    </header>
  );
}

function SectionLabel({ children, id }: { children: ReactNode; id?: string }) {
  return (
    <p className={styles.sectionLabel} id={id}>
      {children}
    </p>
  );
}

function LandingShell() {
  const [featureMode, setFeatureMode] = useState<FeaturesMode>('candidate');
  const featureView = landingFeatures.views[featureMode];
  const [activeStepId, setActiveStepId] = useState(featureView.steps[0].id);
  const activeStep = featureView.steps.find((s) => s.id === activeStepId) ?? featureView.steps[0];

  function changeMode(mode: FeaturesMode) {
    setFeatureMode(mode);
    setActiveStepId(landingFeatures.views[mode].steps[0].id);
  }

  return (
    <div className={styles.page} data-testid="landing-page">
      <a href="#landing-main" className={styles.skipLink}>
        Перейти к содержимому
      </a>
      <LandingHeader />

      <main id="landing-main">
        <section className={styles.hero} aria-labelledby="landing-hero-heading">
          <div className={styles.heroMedia} aria-hidden>
            <img src={landingHero.heroImage} alt="" className={styles.heroArt} />
            <div className={styles.heroScrim} />
          </div>

          <div className={styles.heroInner}>
            <img
              src="/fsp-logo.svg"
              alt="ФСП"
              className={styles.heroLogo}
              width={280}
              height={96}
              decoding="async"
            />
            <p className={styles.heroBrand}>{landingHero.brand}</p>
            <h1 id="landing-hero-heading" className={styles.heroTitle}>
              {landingHero.headline}
            </h1>
            <p className={styles.heroSubtitle}>{landingHero.subtitle}</p>
            <div className={styles.ctaRow}>
              <Link className={styles.btnPrimary} to={landingHero.primaryCta.to}>
                {landingHero.primaryCta.label}
              </Link>
              <Link className={styles.btnSecondary} to={landingHero.secondaryCta.to}>
                {landingHero.secondaryCta.label}
              </Link>
            </div>
            <button
              type="button"
              className={styles.scrollCue}
              onClick={() => scrollToHash(landingHero.scrollTarget)}
              aria-label={landingHero.scrollLabel}
            >
              <span className={styles.scrollLine} aria-hidden />
              {landingHero.scrollLabel}
            </button>
          </div>
        </section>

        <section id={landingHowItWorks.id} className={styles.section} aria-labelledby="how-heading">
          <div className={styles.container}>
            <SectionLabel>{landingHowItWorks.label}</SectionLabel>
            <h2 id="how-heading" className={styles.sectionTitle}>
              {landingHowItWorks.title}
            </h2>
            <ol className={styles.bento}>
              {landingHowItWorks.steps.map((step, index) => (
                <li
                  key={step.id}
                  className={`${styles.bentoItem} ${index === 0 ? styles.bentoHero : ''}`}
                >
                  <p className={styles.bentoNum}>{step.number}</p>
                  <div className={styles.bentoCopy}>
                    <h3>{step.title}</h3>
                    <p>{step.description}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className={`${styles.section} ${styles.sectionAlt}`} aria-label="Превью продукта">
          <div className={styles.container}>
            <ProductPreview />
          </div>
        </section>

        <section id={landingRoles.id} className={styles.section} aria-labelledby="roles-heading">
          <div className={styles.container}>
            <SectionLabel>{landingRoles.label}</SectionLabel>
            <h2 id="roles-heading" className={styles.sectionTitle}>
              {landingRoles.title}
            </h2>
            <div className={styles.roles}>
              {landingRoles.cards.map((card) => (
                <article key={card.id} className={styles.roleCard}>
                  <p className={styles.roleEyebrow}>{card.title}</p>
                  <h3 className={styles.roleTitle}>{card.subtitle}</h3>
                  <ul>
                    {card.features.map((f) => (
                      <li key={f}>{f}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id={landingFeatures.id} className={`${styles.section} ${styles.sectionAlt}`} aria-labelledby="features-heading">
          <div className={styles.container}>
            <div className={styles.featuresLayout}>
              <div className={styles.featuresSticky}>
                <SectionLabel>{landingFeatures.label}</SectionLabel>
                <h2 id="features-heading" className={styles.sectionTitle}>
                  {landingFeatures.title}
                </h2>

                <div className={styles.modeToggle} role="tablist" aria-label="Сценарий платформы">
                  <span className={styles.modeThumb} data-mode={featureMode} aria-hidden />
                  {landingFeatures.modes.map((mode) => (
                    <button
                      key={mode.id}
                      type="button"
                      role="tab"
                      aria-selected={featureMode === mode.id}
                      className={featureMode === mode.id ? styles.modeActive : styles.modeBtn}
                      onClick={() => changeMode(mode.id)}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>

                <p className={styles.featuresSub}>{featureView.subtitle}</p>

                <ol className={styles.stepList}>
                  {featureView.steps.map((step) => (
                    <li key={step.id}>
                      <button
                        type="button"
                        className={`${styles.stepBtn} ${activeStepId === step.id ? styles.stepBtnActive : ''}`}
                        onClick={() => setActiveStepId(step.id)}
                      >
                        <span className={styles.stepNum}>{step.number}</span>
                        <span>
                          <strong>{step.title}</strong>
                          <em>{step.description}</em>
                        </span>
                      </button>
                    </li>
                  ))}
                </ol>
              </div>

              <div className={styles.featuresPreview} aria-live="polite">
                <p className={styles.previewCardLabel}>{activeStep.title}</p>
                <p className={styles.featuresPreviewBody}>{activeStep.description}</p>
                <div className={styles.miniPreview}>
                  <ProductPreview compact mode={featureMode} stepId={activeStepId} />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id={landingCta.id} className={styles.ctaSection} aria-labelledby="cta-heading">
          <div className={styles.container}>
            <div className={styles.ctaBand}>
              <div>
                <h2 id="cta-heading" className={styles.ctaTitle}>
                  {landingCta.title}
                </h2>
                <p className={styles.ctaText}>{landingCta.subtitle}</p>
              </div>
              <Link className={styles.btnPrimary} to={landingCta.cta.to}>
                {landingCta.cta.label}
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.container}>
          <div className={styles.footerMain}>
            <div className={styles.footerBrandCol}>
              <img
                src="/fsp-logo-dark.svg"
                alt="ФСП"
                className={styles.footerLogo}
                width={160}
                height={55}
                decoding="async"
              />
              <p className={styles.footerBrandMark}>
                {landingFooter.brand}
                <span aria-hidden>.</span>
              </p>
              <p className={styles.footerTagline}>{landingFooter.tagline}</p>
              <p className={styles.footerDesc}>{landingFooter.description}</p>
              <p className={styles.footerPillars}>{landingFooter.pillars}</p>
            </div>

            <div className={styles.footerCols}>
              {landingFooter.columns.map((col) => (
                <nav key={col.title} className={styles.footerCol} aria-label={col.title}>
                  <p className={styles.footerColTitle}>{col.title}</p>
                  <ul className={styles.footerList}>
                    {col.links.map((link) => (
                      <li key={link.label}>
                        {'to' in link ? (
                          <Link className={styles.footerLink} to={link.to}>
                            {link.label}
                          </Link>
                        ) : link.external ? (
                          <a
                            className={styles.footerLink}
                            href={link.href}
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {link.label}
                            <span className={styles.footerExt} aria-hidden>
                              ↗
                            </span>
                          </a>
                        ) : (
                          <a
                            className={styles.footerLink}
                            href={link.href}
                            onClick={(e) => {
                              if (link.href.startsWith('#')) {
                                e.preventDefault();
                                scrollToHash(link.href);
                              }
                            }}
                          >
                            {link.label}
                          </a>
                        )}
                      </li>
                    ))}
                  </ul>
                </nav>
              ))}
            </div>
          </div>

          <div className={styles.footerBar}>
            <p className={styles.footerCopy}>{landingFooter.meta.copyright}</p>
            <p className={styles.footerNote}>{landingFooter.meta.note}</p>
            <Link className={styles.footerBarLink} to="/ui-kit">
              Дизайн-система
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export function LandingPage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <Loader />;
  if (isAuthenticated && user) return <Navigate to={roleHome(user.role)} replace />;
  return <LandingShell />;
}
