import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { Loader } from '@/shared/ui';
import {
  landingCta,
  landingDock,
  landingFeatures,
  landingHero,
  landingHowItWorks,
  landingRoles,
  type FeaturesMode,
} from '@/pages/landing/content';
import styles from './LandingPage.module.css';

type Theme = 'light' | 'dark';

const THEME_KEY = 'resonance-landing-theme';
const SECTION_IDS = landingDock.map((item) => item.id);
const BENTO_TONES = ['bentoTone0', 'bentoTone1', 'bentoTone2', 'bentoTone3'] as const;

function readTheme(): Theme {
  try {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
  } catch {
    /* ignore */
  }
  return 'light';
}

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

function ProgressRing({ value }: { value: number }) {
  const r = 28;
  const c = 2 * Math.PI * r;
  const offset = c - (value / 100) * c;
  return (
    <svg className={styles.ring} viewBox="0 0 72 72" aria-hidden>
      <circle cx="36" cy="36" r={r} className={styles.ringTrack} />
      <circle
        cx="36"
        cy="36"
        r={r}
        className={styles.ringValue}
        strokeDasharray={c}
        strokeDashoffset={offset}
      />
    </svg>
  );
}

function ProductPreview({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`${styles.preview} ${compact ? styles.previewCompact : ''}`} aria-hidden>
      <aside className={styles.previewAside}>
        <p className={styles.previewBrand}>
          Resonance<span>.</span>
        </p>
        <nav className={styles.previewNav}>
          {['Talent Pool', 'Вакансии', 'Shortlist', 'Офферы'].map((label, i) => (
            <div key={label} className={i === 0 ? styles.previewNavActive : styles.previewNavItem}>
              {label}
            </div>
          ))}
        </nav>
      </aside>
      <div className={styles.previewMain}>
        <div className={styles.previewHead}>
          <div>
            <p className={styles.previewTitle}>Talent Pool</p>
            <p className={styles.previewMuted}>Match Score по вакансии Senior Backend</p>
          </div>
          <span className={styles.previewChip}>ФСП</span>
        </div>
        <div className={styles.previewGrid}>
          <div className={styles.previewCard}>
            <p className={styles.previewCardLabel}>Top match</p>
            <div className={styles.previewScoreRow}>
              <ProgressRing value={92} />
              <div>
                <p className={styles.previewScore}>92%</p>
                <p className={styles.previewMuted}>Match Score</p>
              </div>
            </div>
            <p className={styles.previewAccent}>Go · PostgreSQL · ФСП verified</p>
          </div>
          <div className={styles.previewCard}>
            <p className={styles.previewCardLabel}>Кандидаты</p>
            <ul className={styles.previewList}>
              {[
                { name: 'Алина К.', score: '92%' },
                { name: 'Максим Р.', score: '84%' },
                { name: 'Игорь С.', score: '77%' },
              ].map((row) => (
                <li key={row.name}>
                  <span>{row.name}</span>
                  <strong>{row.score}</strong>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

function ThemeToggle({ theme, onToggle }: { theme: Theme; onToggle: () => void }) {
  return (
    <button
      type="button"
      className={styles.themeToggle}
      onClick={onToggle}
      aria-label={theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
    >
      {theme === 'dark' ? (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="2" />
          <path
            d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path
            d="M21 14.5A8.5 8.5 0 0 1 9.5 3 7 7 0 1 0 21 14.5Z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
      )}
    </button>
  );
}

function LandingHeader({
  theme,
  onToggleTheme,
}: {
  theme: Theme;
  onToggleTheme: () => void;
}) {
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
        setScrolled(window.scrollY > 24);
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

  return (
    <header className={`${styles.header} ${scrolled || menuOpen ? styles.headerSolid : ''}`}>
      <div className={styles.headerInner}>
        <Link to="/" className={styles.logo} aria-label={`${landingHero.brand} — ${landingHero.brandTagline}`}>
          <span className={styles.logoMark}>{landingHero.brand}</span>
          <span className={styles.logoTag}>{landingHero.brandTagline}</span>
        </Link>

        <div className={styles.headerActions}>
          <div className={styles.headerAuth}>
            <Link className={styles.btnSecondary} to="/login">
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
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
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
        <div id={menuId} ref={panelRef} className={styles.mobileMenu} role="dialog" aria-modal="true" aria-label="Мобильное меню">
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
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            <Link className={styles.btnSecondary} to="/login" onClick={() => setMenuOpen(false)}>
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

function LandingDock({
  theme,
  onToggleTheme,
}: {
  theme: Theme;
  onToggleTheme: () => void;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => setActiveId(getActiveSectionId(SECTION_IDS)));
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', onScroll);
    };
  }, []);

  return (
    <div className={styles.dockWrap}>
      <div className={styles.dock}>
        <nav className={styles.dockNav} aria-label="Разделы лендинга">
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
          <a
            href="#landing-main"
            className={`${styles.dockLink} ${styles.dockHome}`}
            onClick={(e) => {
              e.preventDefault();
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          >
            Главная
          </a>
          {landingDock.map((item) => (
            <a
              key={item.id}
              href={item.href}
              className={`${styles.dockLink} ${activeId === item.id ? styles.dockLinkActive : ''}`}
              onClick={(e) => {
                e.preventDefault();
                scrollToHash(item.href);
              }}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <Link to={landingHero.primaryCta.to} className={styles.dockCta}>
          {landingHero.primaryCta.label}
        </Link>
      </div>
    </div>
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
  const [theme, setTheme] = useState<Theme>(readTheme);
  const [featureMode, setFeatureMode] = useState<FeaturesMode>('candidate');
  const featureView = landingFeatures.views[featureMode];
  const [activeStepId, setActiveStepId] = useState(featureView.steps[0].id);
  const activeStep = featureView.steps.find((s) => s.id === activeStepId) ?? featureView.steps[0];

  useEffect(() => {
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* ignore */
    }
  }, [theme]);

  function toggleTheme() {
    setTheme((t) => (t === 'light' ? 'dark' : 'light'));
  }

  function changeMode(mode: FeaturesMode) {
    setFeatureMode(mode);
    setActiveStepId(landingFeatures.views[mode].steps[0].id);
  }

  return (
    <div className={styles.page} data-theme={theme} data-testid="landing-page">
      <a href="#landing-main" className={styles.skipLink}>
        Перейти к содержимому
      </a>
      <LandingHeader theme={theme} onToggleTheme={toggleTheme} />
      <LandingDock theme={theme} onToggleTheme={toggleTheme} />

      <main id="landing-main">
        <section className={styles.hero} aria-labelledby="landing-hero-heading">
          <div className={styles.heroStage}>
            <div className={styles.heroBg} aria-hidden>
              <img src="/resonance_hero.svg" alt="" className={styles.heroArt} />
            </div>

            <div className={styles.heroInner}>
              <div className={styles.heroGrid}>
                <div className={styles.heroLeft}>
                  <h1
                    id="landing-hero-heading"
                    className={styles.heroTitle}
                    aria-label={landingHero.label}
                  >
                    {landingHero.lines.map((line, i) => (
                      <span
                        key={line}
                        className={styles.heroLine}
                        style={{ animationDelay: `${0.06 + i * 0.08}s` }}
                      >
                        {line}
                      </span>
                    ))}
                  </h1>

                  <div className={styles.ctaRow}>
                    <Link className={styles.btnPrimary} to={landingHero.primaryCta.to}>
                      {landingHero.primaryCta.label}
                    </Link>
                    <Link className={styles.btnSecondary} to={landingHero.secondaryCta.to}>
                      {landingHero.secondaryCta.label}
                    </Link>
                  </div>

                  <div className={styles.scrollWrap}>
                    <button
                      type="button"
                      className={styles.scrollCue}
                      onClick={() => scrollToHash(landingHero.scrollTarget)}
                      aria-label={`${landingHero.scrollLabel} — дальше`}
                    >
                      <span className={styles.scrollDot} />
                      <span>{landingHero.scrollLabel}</span>
                    </button>
                  </div>
                </div>

                <div className={styles.heroRight}>
                  <div className={styles.heroSpacer} aria-hidden />
                  <p className={styles.heroSubtitle}>{landingHero.subtitle}</p>
                </div>
              </div>
            </div>
          </div>

          <div id="hero-continue" className={styles.heroPeekWrap}>
            <div className={styles.heroPeek}>
              <ProductPreview />
              <div className={styles.heroPeekFade} aria-hidden />
            </div>
          </div>
        </section>

        <section id={landingHowItWorks.id} className={styles.section} aria-labelledby="how-heading">
          <div className={styles.container}>
            <SectionLabel id="how-heading">{landingHowItWorks.label}</SectionLabel>
            <ol className={styles.bento}>
              {landingHowItWorks.steps.map((step, index) => (
                <li key={step.id} className={`${styles.bentoItem} ${styles[BENTO_TONES[index]]}`}>
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

        <section
          id={landingRoles.id}
          className={`${styles.section} ${styles.sectionTight}`}
          aria-labelledby="roles-heading"
        >
          <div className={styles.containerWide}>
            <SectionLabel>Для кого</SectionLabel>
            <h2 id="roles-heading" className={styles.displayTitle}>
              {landingRoles.titleLines.map((line) => (
                <span key={line}>{line}</span>
              ))}
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

        <section id={landingFeatures.id} className={styles.section} aria-labelledby="features-heading">
          <div className={styles.container}>
            <div className={styles.featuresLayout}>
              <div className={styles.featuresSticky}>
                <SectionLabel>{landingFeatures.label}</SectionLabel>
                <h2 id="features-heading" className={`${styles.displayTitle} ${styles.displayUpper}`}>
                  {landingFeatures.titleLines.map((line) => (
                    <span key={line}>{line}</span>
                  ))}
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
                  <ProductPreview compact />
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id={landingCta.id} className={styles.ctaSection} aria-labelledby="cta-heading">
          <div className={styles.container}>
            <div className={styles.ctaBand}>
              <h2 id="cta-heading" className={styles.ctaTitle}>
                {landingCta.title}
              </h2>
              <div className={styles.ctaSide}>
                <p>{landingCta.subtitle}</p>
                <Link className={styles.btnPrimary} to={landingCta.cta.to}>
                  {landingCta.cta.label}
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className={styles.footer}>
        <div className={styles.containerWide}>
          <div className={styles.footerBrand}>
            <p className={styles.logoMark}>{landingHero.brand}</p>
            <p className={styles.footerMuted}>Match Score · ФСП · контакты после accept</p>
          </div>
          <nav className={styles.footerNav} aria-label="Документация">
            <Link className={styles.footerLink} to="/ui-kit">
              UI Kit
            </Link>
          </nav>
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
