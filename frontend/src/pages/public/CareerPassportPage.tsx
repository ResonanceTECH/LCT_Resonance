import { useQuery } from '@tanstack/react-query';
import { QRCodeSVG } from 'qrcode.react';
import { useParams } from 'react-router-dom';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { FSPVerificationBadge } from '@/entities/ui/FSPVerificationBadge';
import { publicApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import {
  formatReadiness,
  formatSpecialization,
} from '@/shared/lib/formatters';
import { Badge, ErrorState, Loader } from '@/shared/ui';
import styles from './CareerPassportPage.module.css';

/** Scannable QR code of the passport link. */
export function QrCode({ value, size = 140 }: { value: string; size?: number }) {
  return (
    <QRCodeSVG
      value={value}
      size={size}
      marginSize={2}
      fgColor="#1B1C21"
      role="img"
      aria-label={`QR на публичный профиль: ${value}`}
      data-testid="passport-qr"
      data-url={value}
    />
  );
}

export function CareerPassportPage() {
  const { slug = '' } = useParams();
  const query = useQuery({
    queryKey: ['public-passport', slug],
    queryFn: () => publicApi.passport(slug),
    enabled: Boolean(slug),
    retry: false,
  });

  if (query.isLoading) return <Loader label="Загружаем карьерный паспорт..." />;
  if (query.isError || !query.data) {
    return (
      <div className="page">
        <ErrorState
          title="Паспорт не найден"
          description={getErrorMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      </div>
    );
  }

  const { profile, achievements, radar, publicUrl } = query.data;
  const role =
    profile.desiredPosition ?? formatSpecialization(profile.specialization);

  return (
    <div className={styles.shell}>
      <header className={styles.topbar}>
        <div className={styles.brand}>ФСП Talent · Карьерный паспорт</div>
        <FSPVerificationBadge label="Публичный профиль" />
      </header>

      <main className={styles.main}>
        <section className={styles.hero} aria-labelledby="passport-heading">
          <div className={styles.heroInfo}>
            <div className={styles.heroTop}>
              <h1 id="passport-heading" className={styles.heroTitle}>
                {profile.fullName}
              </h1>
              <Badge tone="accent">{formatReadiness(profile.readiness)}</Badge>
            </div>
            <p className={styles.heroMeta}>
              {role}
              {profile.city ? ` · ${profile.city}` : ''}
            </p>
            {profile.about ? <p className={styles.heroAbout}>{profile.about}</p> : null}
            <p className={styles.heroNote}>
              Публичный карьерный паспорт. Навыки, тесты и достижения ФСП — без контактов до
              согласия кандидата.
            </p>
          </div>

          <aside className={styles.heroQr}>
            <p className={styles.qrLabel}>QR-код профиля</p>
            <QrCode value={publicUrl} size={132} />
            <p className={styles.qrLink}>{publicUrl}</p>
          </aside>
        </section>

        <CandidateProfileView
          mode="employer"
          profile={profile}
          achievements={achievements}
          hideIntro
        />
        <SkillRadar radar={radar} />
      </main>
    </div>
  );
}
