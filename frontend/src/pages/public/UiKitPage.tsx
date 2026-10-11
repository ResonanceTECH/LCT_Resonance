import { useEffect, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
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
  Select,
  Skeleton,
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
  { id: 'badges', label: 'Badges' },
  { id: 'domain', label: 'Domain' },
  { id: 'match', label: 'Match & Radar' },
  { id: 'testing', label: 'Testing' },
  { id: 'offer', label: 'Offer form' },
  { id: 'landing', label: 'Landing' },
  { id: 'rules', label: 'Rules' },
] as const;

const COLORS = [
  { name: 'brand-primary', value: '#402FFF', varName: '--brand-primary' },
  { name: 'brand-red', value: '#EC1D35', varName: '--brand-red' },
  { name: 'background-page', value: '#F7F7FA', varName: '--background-page' },
  { name: 'background-card', value: '#FFFFFF', varName: '--background-card' },
  { name: 'text-primary', value: '#1B1C21', varName: '--text-primary' },
  { name: 'text-secondary', value: '#565966', varName: '--text-secondary' },
  { name: 'primary-50', value: '#F2F0FF', varName: '--primary-50' },
  { name: 'primary-600', value: '#3324E6', varName: '--primary-600' },
  { name: 'success-main', value: '#16834A', varName: '--success-main' },
  { name: 'warning-main', value: '#A9650C', varName: '--warning-main' },
  { name: 'error-main', value: '#D8273C', varName: '--error-main' },
  { name: 'info-main', value: '#2764C5', varName: '--info-main' },
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

export function UiKitPage() {
  const [tab, setTab] = useState('overview');
  const [modalOpen, setModalOpen] = useState(false);
  const [checked, setChecked] = useState(true);
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
          <div className={styles.brand}>FSP Talent · UI Kit</div>
          <p className={styles.brandMeta}>Living style guide · tokens · shared · domain</p>
        </div>
        <div className={styles.topActions}>
          <Link to="/" className={styles.topLinkGhost}>
            На лендинг
          </Link>
          <Link to="/login" className={styles.topLinkSecondary}>
            Demo-вход
          </Link>
        </div>
      </header>

      <div className={styles.shell}>
        <div className={styles.hero}>
          <p className={styles.heroEyebrow}>Design system</p>
          <h1 className={styles.heroTitle}>
            Всё для
            <br />
            дальнейшей разработки
          </h1>
          <p className={styles.heroLead}>
            Визуальный каталог токенов, shared UI и domain-компонентов. Копируй паттерны, не выдумывай
            вторую палитру. Backend owns truth.
          </p>
          <div className={styles.heroStats}>
            <div className={styles.stat}>
              <span className={styles.statValue}>{COLORS.length}</span>
              <span className={styles.statLabel}>color tokens</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>14</span>
              <span className={styles.statLabel}>shared UI</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>16</span>
              <span className={styles.statLabel}>domain UI</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>6</span>
              <span className={styles.statLabel}>view states</span>
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

          <Section id="foundations" title="Foundations" hint="Токены из src/styles/global.css">
            <Canvas label="Color tokens">
              <div className={styles.swatches}>
                {COLORS.map((c) => (
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
            </Canvas>
            <div className={styles.grid3} style={{ marginTop: '1rem' }}>
              <Canvas label="Radius">
                <div className={styles.row}>
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--accent-soft)',
                    }}
                  />
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 'var(--radius)',
                      background: 'var(--accent-soft)',
                    }}
                  />
                  <div
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 999,
                      background: 'var(--accent)',
                    }}
                  />
                </div>
                <p className={styles.typeMeta}>--radius-sm · --radius · pill 999</p>
              </Canvas>
              <Canvas label="Shadow">
                <div
                  style={{
                    height: 72,
                    borderRadius: 'var(--radius)',
                    background: '#fff',
                    boxShadow: 'var(--shadow)',
                  }}
                />
                <p className={styles.typeMeta}>--shadow</p>
              </Canvas>
              <Canvas label="Import">
                <pre className={styles.importBox}>{`import { Button, Input, Badge } from '@/shared/ui';
import { MatchScore } from '@/entities/ui/MatchScore';`}</pre>
              </Canvas>
            </div>
          </Section>

          <Section id="typography" title="Typography" hint="JetBrains Mono (H1–H3, KPI) · Golos Text (UI body)">
            <Canvas label="Type scale">
              <div className={styles.typeSample}>
                <p className={styles.displaySample}>JetBrains Mono — display</p>
                <p className={styles.typeMeta}>h1–h3 · KPI · brand · landing hero</p>
              </div>
              <div className={styles.typeSample}>
                <p className={styles.bodySample}>Golos Text — body UI. Кандидат с ФСП. Match Score. Контакты после accept.</p>
                <p className={styles.typeMeta}>14px / 22 · controls · labels · descriptions</p>
              </div>
              <div className={styles.typeSample}>
                <p className={styles.mutedSample}>muted — вторичный текст, подсказки, метаданные</p>
                <p className={styles.typeMeta}>color: var(--text-secondary)</p>
              </div>
            </Canvas>
          </Section>

          <Section id="buttons" title="Buttons" hint="shared/ui/Button · variants">
            <Canvas label="Variants">
              <div className={styles.row}>
                <Button type="button">Primary</Button>
                <Button type="button" variant="secondary">
                  Secondary
                </Button>
                <Button type="button" variant="ghost">
                  Ghost
                </Button>
                <Button type="button" variant="danger">
                  Danger
                </Button>
              </div>
            </Canvas>
            <div style={{ height: '0.85rem' }} />
            <Canvas label="States">
              <div className={styles.row}>
                <Button type="button" disabled>
                  Disabled
                </Button>
                <Button type="button" variant="secondary" disabled>
                  Disabled secondary
                </Button>
                <span className={styles.codeChip}>disabled во время mutation</span>
              </div>
            </Canvas>
          </Section>

          <Section id="forms" title="Forms" hint="Input · Select · Textarea · Checkbox">
            <div className={styles.grid2}>
              <Canvas label="Controls">
                <div className={styles.stack}>
                  <Input label="Email" name="kit-email" placeholder="candidate@demo.ru" defaultValue="candidate@demo.ru" />
                  <Input label="С ошибкой" name="kit-error" error="Обязательное поле" />
                  <Select
                    label="Роль"
                    name="kit-role"
                    options={[
                      { value: 'candidate', label: 'Кандидат' },
                      { value: 'employer', label: 'Работодатель' },
                    ]}
                  />
                  <Textarea label="О себе" name="kit-about" rows={3} defaultValue="Frontend, React, дизайн-системы." />
                  <Checkbox
                    label="Открыт к офферам"
                    name="kit-ready"
                    checked={checked}
                    onChange={(e) => setChecked(e.target.checked)}
                  />
                </div>
              </Canvas>
              <Canvas label="Tabs">
                <Tabs
                  tabs={[
                    { id: 'overview', label: 'Обзор' },
                    { id: 'fsp', label: 'ФСП' },
                    { id: 'tests', label: 'Тесты' },
                  ]}
                  value={tab}
                  onChange={setTab}
                />
                <p style={{ marginTop: '1rem', marginBottom: 0 }}>
                  Активная вкладка: <strong>{tab}</strong>
                </p>
              </Canvas>
            </div>
          </Section>

          <Section id="feedback" title="Feedback & states" hint="Каждый data view: loading · success · empty · error · disabled · success action">
            <div className={styles.stateGrid}>
              <Canvas label="Loading">
                <Loader label="Загрузка пула кандидатов…" />
                <div className={styles.stack} style={{ marginTop: '1rem' }}>
                  <Skeleton height={18} width="70%" />
                  <Skeleton height={14} />
                  <Skeleton height={14} width="85%" />
                </div>
              </Canvas>
              <Canvas label="Empty">
                <EmptyState
                  title="Кандидаты не найдены"
                  description="Смягчите фильтры или обновите пул кандидатов."
                  action={
                    <Button type="button" variant="secondary">
                      Сбросить фильтры
                    </Button>
                  }
                />
              </Canvas>
              <Canvas label="Error">
                <ErrorState
                  title="Не удалось загрузить"
                  description="Сервер временно недоступен."
                  onRetry={() => undefined}
                />
              </Canvas>
              <Canvas label="Progress + Modal">
                <p className={styles.canvasLabel} style={{ marginBottom: '0.5rem' }}>
                  Profile completeness 72%
                </p>
                <ProgressBar value={72} />
                <div style={{ marginTop: '1rem' }}>
                  <Button type="button" onClick={() => setModalOpen(true)}>
                    Открыть Modal
                  </Button>
                </div>
              </Canvas>
            </div>
            <Modal open={modalOpen} title="Отправить оффер" onClose={() => setModalOpen(false)}>
              <p>Modal — контейнер для форм и подтверждений. Backdrop закрывает.</p>
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

          <Section id="badges" title="Badges & markers" hint="Badge tones · Grade · FSP · Skills · Salary">
            <Canvas label="Badge tones">
              <div className={styles.row}>
                <Badge>default</Badge>
                <Badge tone="accent">accent / new</Badge>
                <Badge tone="success">success / accepted</Badge>
                <Badge tone="warn">warn / viewed</Badge>
                <Badge tone="danger">danger / declined</Badge>
                <Badge tone="fsp">fsp</Badge>
              </div>
            </Canvas>
            <div className={styles.grid2} style={{ marginTop: '1rem' }}>
              <Canvas label="Domain badges">
                <div className={styles.row}>
                  <GradeBadge grade="middle" />
                  <GradeBadge grade="senior" />
                  <FSPVerificationBadge />
                  <FSPVerificationBadge label="FSP Verified" />
                </div>
                <div className={styles.row} style={{ marginTop: '0.85rem' }}>
                  {['React', 'TypeScript', 'Go', 'PostgreSQL'].map((skill) => (
                    <SkillBadge key={skill} skill={skill} />
                  ))}
                </div>
              </Canvas>
              <Canvas label="SalaryRange">
                <p style={{ margin: 0, fontSize: '1.25rem' }}>
                  <strong>
                    <SalaryRange from={250000} to={320000} currency="RUB" />
                  </strong>
                </p>
                <p className={styles.typeMeta}>formatters · не считать на клиенте бизнес-логику</p>
              </Canvas>
            </div>
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
            <div style={{ marginTop: '1rem' }}>
              <Canvas label="CandidateProfileView · employer mode">
                <CandidateProfileView
                  profile={profile}
                  achievements={fspByCandidate[profile.id] ?? []}
                  match={match}
                  mode="employer"
                />
              </Canvas>
            </div>
            <div style={{ marginTop: '1rem' }}>
              <Canvas label="Card atom">
                <Card>
                  <h3 style={{ marginTop: 0 }}>Card</h3>
                  <p style={{ marginBottom: 0 }}>
                    Контейнер взаимодействия. В hero лендинга — нельзя.
                  </p>
                </Card>
              </Canvas>
            </div>
          </Section>

          <Section id="match" title="Оценка соответствия и радар" hint="Только отображение данных с сервера">
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

          <Section id="landing" title="Landing surface" hint="FSP Minimal Tech · shared tokens · LandingPage.module.css">
            <div className={styles.landingStrip}>
              <div className={styles.landingLight}>
                <div>
                  <p className={styles.landingBrand}>FSP Talent</p>
                  <p style={{ margin: '0.5rem 0 0', opacity: 0.75 }}>
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
                  <p style={{ margin: '0.5rem 0 0', opacity: 0.75 }}>
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
              Landing: sticky topbar 72px, bento 16px, buttons 12px / 44px. Без dark-theme toggle.
            </p>
          </Section>

          <Section id="rules" title="Rules" hint="Не ломай границы ТЗ">
            <div className={styles.principles}>
              {[
                ['Backend owns truth', 'Match Score, test scores, FSP, contacts — только DTO.'],
                ['No false claims', '«не указан в профиле» ≠ «не умеет».'],
                ['FSP ≠ self-reported', 'FSPVerificationBadge только на данных ФСП.'],
                ['Domain components are dumb', 'Fetch только в pages/hooks.'],
                ['6 states', 'loading · success · empty · error · disabled · action success.'],
                ['Cards for interaction', 'Hero лендинга — без карточек и stats.'],
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
              Спека в markdown: <code className={styles.codeChip}>frontend/UI_KIT.md</code> · этот экран — visual
              source of truth для разработки.
            </p>
          </Section>
        </div>
      </div>
    </div>
  );
}
