import { useQuery } from '@tanstack/react-query';
import { QRCodeSVG } from 'qrcode.react';
import { useParams } from 'react-router-dom';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { FSPVerificationBadge } from '@/entities/ui/FSPVerificationBadge';
import { publicApi } from '@/shared/api/endpoints';
import { getErrorMessage } from '@/shared/api/errors';
import { ErrorState, Loader } from '@/shared/ui';

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

  if (query.isLoading) return <Loader label="Загружаем Career Passport..." />;
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

  return (
    <div className="landing">
      <header className="topbar">
        <div className="brand">FSP Talent · Career Passport</div>
        <FSPVerificationBadge label="Public profile" />
      </header>
      <main className="page stack">
        <div className="page-header">
          <div>
            <h1>{profile.fullName}</h1>
            <p>Публичный паспорт кандидата. Контакты скрыты.</p>
          </div>
          <div className="section-card" style={{ textAlign: 'center' }}>
            <QrCode value={publicUrl} />
            <p className="muted" style={{ marginBottom: 0, fontSize: '0.85rem', wordBreak: 'break-all' }}>
              {publicUrl}
            </p>
          </div>
        </div>
        <CandidateProfileView mode="employer" profile={profile} achievements={achievements} />
        <SkillRadar radar={radar} />
      </main>
    </div>
  );
}
