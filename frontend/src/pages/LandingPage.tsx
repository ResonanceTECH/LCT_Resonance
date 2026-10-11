import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { roleHome, useAuth } from '@/features/auth/AuthContext';
import { Accordion, Loader } from '@/shared/ui';
import {
  landingCta,
  landingDock,
  landingFaq,
  landingFeatures,
  landingFooter,
  landingHero,
  landingHowItWorks,
  landingRoles,
  type FeaturesMode,
  type FooterLink,
} from '@/pages/landing/content';
import styles from './LandingPage.module.css';

const SECTION_IDS = landingDock.map((item) => item.id);

function isRouteFooterLink(link: FooterLink): link is Extract<FooterLink, { to: string }> {
  return 'to' in link;
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

function MatchRing({ value, size = 72 }: { value: number; size?: number }) {
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

/** Focused product slices — not a full cabinet clone. */
function DemoPassport() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Цифровой паспорт</p>
      <div className={styles.demoPassport}>
        <div className={styles.demoPassportMain}>
          <div className={styles.demoPerson}>
            <span className={styles.uiAvatar}>АК</span>
            <div>
              <p className={styles.demoTitle}>Алина К.</p>
              <p className={styles.demoMeta}>Бэкенд · средний · гибрид</p>
            </div>
          </div>
          <div className={styles.demoBadgeRow}>
            <span className={styles.uiBadgeOk}>ФСП</span>
            <span className={styles.uiBadgeAccent}>Тест пройден</span>
          </div>
          <div className={styles.demoSkillBlock}>
            <p className={styles.demoLabel}>Подтверждено тестом</p>
            <div className={styles.uiSkills}>
              {['Go', 'PostgreSQL', 'Docker'].map((s) => (
                <span key={s} className={styles.uiSkill}>
                  {s}
                </span>
              ))}
            </div>
          </div>
          <div className={styles.demoSkillBlock}>
            <p className={styles.demoLabel}>Заявлено кандидатом</p>
            <div className={styles.uiSkills}>
              <span className={styles.uiSkillMute}>Kafka</span>
              <span className={styles.uiSkillMute}>gRPC</span>
            </div>
          </div>
        </div>
        <aside className={styles.demoPassportSide}>
          <div className={styles.demoQr} aria-hidden>
            <span />
            <span />
            <span />
            <span />
          </div>
          <p className={styles.demoMeta}>Контакты скрыты</p>
        </aside>
      </div>
    </div>
  );
}

function DemoMatch() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Совпадение по навыкам</p>
      <div className={styles.demoMatchHead}>
        <MatchRing value={92} />
        <div>
          <p className={styles.demoMatchValue}>92%</p>
          <p className={styles.demoMeta}>к вакансии «Старший бэкенд»</p>
        </div>
      </div>
      <ul className={styles.demoReasons}>
        <li className={styles.demoReasonOk}>Go и PostgreSQL подтверждены тестом</li>
        <li className={styles.demoReasonOk}>Есть достижения ФСП по алгоритмам</li>
        <li className={styles.demoReasonWarn}>Kafka не указана в профиле</li>
      </ul>
      <div className={styles.demoBars}>
        {[
          { name: 'Go', need: 90, have: 92 },
          { name: 'PostgreSQL', need: 85, have: 88 },
          { name: 'Kafka', need: 70, have: 0 },
        ].map((row) => (
          <div key={row.name} className={styles.demoBarRow}>
            <span>{row.name}</span>
            <div className={styles.demoBarTrack}>
              <i style={{ width: `${row.need}%` }} className={styles.demoBarNeed} />
              <b style={{ width: `${row.have}%` }} className={styles.demoBarHave} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DemoVacancy() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Вакансия</p>
      <p className={styles.demoTitle}>Старший инженер бэкенда</p>
      <p className={styles.demoMeta}>ООО «Сигнал» · удалённо · полная занятость</p>
      <p className={styles.demoPay}>280–350 тыс ₽</p>
      <div className={styles.uiSkills}>
        {['Go', 'PostgreSQL', 'Kafka'].map((s) => (
          <span key={s} className={styles.uiSkill}>
            {s}
          </span>
        ))}
      </div>
      <div className={styles.demoVacancyFoot}>
        <span className={styles.uiBadgeAccent}>Уровень: старший</span>
        <span className={styles.demoMeta}>Вилка видна до контактов</span>
      </div>
    </div>
  );
}

function DemoFsp() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Достижения ФСП</p>
      <p className={styles.demoTitle}>Не путаем с самооценкой</p>
      <div className={styles.demoList}>
        {[
          { title: 'Олимпиада ФСП', meta: 'Алгоритмы · топ-10%', ok: true },
          { title: 'Рейтинг дисциплины', meta: 'Активен · 2025', ok: true },
          { title: 'Kafka в резюме', meta: 'Заявлено кандидатом', ok: false },
        ].map((row) => (
          <div key={row.title} className={styles.demoListItem}>
            <div>
              <p className={styles.demoListTitle}>{row.title}</p>
              <p className={styles.demoMeta}>{row.meta}</p>
            </div>
            <span className={row.ok ? styles.uiBadgeOk : styles.uiBadgeMute}>
              {row.ok ? 'ФСП' : 'Заявлено'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DemoTest() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Результат теста</p>
      <div className={styles.demoMatchHead}>
        <MatchRing value={82} />
        <div>
          <p className={styles.demoMatchValue}>82 / 100</p>
          <p className={styles.demoMeta}>Уровень «средний» подтверждён</p>
        </div>
      </div>
      <div className={styles.demoList}>
        {[
          ['Go', 'подтверждён'],
          ['PostgreSQL', 'подтверждён'],
          ['Kafka', 'не в тесте'],
        ].map(([skill, status]) => (
          <div key={skill} className={styles.demoListItem}>
            <p className={styles.demoListTitle}>{skill}</p>
            <span className={status === 'подтверждён' ? styles.uiBadgeOk : styles.uiBadgeMute}>
              {status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function DemoOffer() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Предложение</p>
      <p className={styles.demoTitle}>Старший бэкенд · 300 тыс ₽</p>
      <p className={styles.demoMeta}>Удалённо · соответствие 92%</p>
      <div className={styles.demoLock}>
        <p className={styles.demoListTitle}>Контакты закрыты</p>
        <p className={styles.demoMeta}>Почта и телеграм откроются только после согласия кандидата</p>
      </div>
      <div className={styles.demoActions}>
        <span className={styles.uiBtnPrimary}>Принять</span>
        <span className={styles.uiBtnGhost}>Отклонить</span>
      </div>
    </div>
  );
}

function DemoCompare() {
  return (
    <div className={styles.demo}>
      <p className={styles.demoEyebrow}>Сравнение кандидатов</p>
      <div className={styles.demoCompare}>
        {[
          { name: 'Алина К.', score: 92, skills: 'Go · ФСП · тест' },
          { name: 'Максим Р.', score: 84, skills: 'Python · тест' },
        ].map((c) => (
          <div key={c.name} className={styles.demoCompareCard}>
            <p className={styles.demoListTitle}>{c.name}</p>
            <p className={styles.demoMatchValue}>{c.score}%</p>
            <p className={styles.demoMeta}>{c.skills}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function previewDemo(mode: FeaturesMode, stepId: string) {
  if (mode === 'candidate') {
    if (stepId === 'fsp') return <DemoFsp />;
    if (stepId === 'tests') return <DemoTest />;
    if (stepId === 'offers') return <DemoOffer />;
    return <DemoPassport />;
  }
  if (stepId === 'vacancy') return <DemoVacancy />;
  if (stepId === 'compare') return <DemoCompare />;
  if (stepId === 'offer') return <DemoOffer />;
  return <DemoMatch />;
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
  const resolvedStep = stepId ?? (mode === 'candidate' ? 'profile' : 'pool');

  return (
    <div
      className={`${styles.preview} ${compact ? styles.previewCompact : ''}`}
      data-mode={mode}
      aria-hidden
    >
      <div className={styles.previewMain} key={`${mode}-${resolvedStep}`}>
        {previewDemo(mode, resolvedStep)}
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
              <div className={styles.featuresIntro}>
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
              </div>

              <div className={styles.featuresPreview} aria-live="polite">
                <ProductPreview compact mode={featureMode} stepId={activeStepId} />
              </div>

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
          </div>
        </section>

        <section id={landingFaq.id} className={`${styles.section} ${styles.sectionAlt}`} aria-labelledby="faq-heading">
          <div className={styles.container}>
            <SectionLabel>{landingFaq.label}</SectionLabel>
            <h2 id="faq-heading" className={styles.sectionTitle}>
              {landingFaq.title}
            </h2>
            <div className={styles.faqList}>
              <Accordion
                columns={2}
                allowMultiple
                items={landingFaq.items.map((item) => ({
                  id: item.id,
                  title: item.question,
                  content: <p>{item.answer}</p>,
                }))}
                defaultOpenId={landingFaq.items[0]?.id}
              />
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
            </div>

            <div className={styles.footerCols}>
              {landingFooter.columns.map((col) => (
                <nav key={col.title} className={styles.footerCol} aria-label={col.title}>
                  <p className={styles.footerColTitle}>{col.title}</p>
                  <ul className={styles.footerList}>
                    {col.links.map((link) => (
                      <li key={link.label}>
                        {isRouteFooterLink(link) ? (
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
            <p className={styles.footerNote}>
              {landingFooter.meta.notePrefix}{' '}
              <a
                className={styles.footerNoteLink}
                href={landingFooter.meta.noteLink.href}
                target="_blank"
                rel="noopener noreferrer"
              >
                {landingFooter.meta.noteLink.label}
              </a>
            </p>
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
