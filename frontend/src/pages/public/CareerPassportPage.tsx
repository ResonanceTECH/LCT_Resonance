import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { CandidateProfileView } from '@/entities/ui/CandidateProfile';
import { SkillRadar } from '@/entities/ui/SkillRadar';
import { FSPVerificationBadge } from '@/entities/ui/FSPVerificationBadge';
import { apiClient } from '@/shared/api/client';
import type { CandidateProfile, FspAchievement, SkillRadar as SkillRadarData } from '@/entities/types';
import { getErrorMessage } from '@/shared/api/errors';
import { ErrorState, Loader } from '@/shared/ui';

type PublicPassport = {
  profile: CandidateProfile;
  achievements: FspAchievement[];
  radar: SkillRadarData;
  publicUrl: string;
};

function publicPassportApi(slug: string) {
  return apiClient<PublicPassport>(`/public/passports/${slug}`, { auth: false });
}

/** Simple QR as SVG (no external deps) — encodes public URL. */
export function QrCode({ value, size = 140 }: { value: string; size?: number }) {
  // Deterministic pseudo-QR pattern from URL hash — placeholder visual for MVP.
  // Real QR generation stays Backend responsibility if needed later.
  const cells = 21;
  const cell = size / cells;
  const hash = Array.from(value).reduce((acc, ch) => (acc * 31 + ch.charCodeAt(0)) >>> 0, 7);
  const bits: boolean[] = [];
  let state = hash;
  for (let i = 0; i < cells * cells; i += 1) {
    state = (state * 1664525 + 1013904223) >>> 0;
    bits.push(state % 3 === 0);
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      role="img"
      aria-label={`QR на публичный профиль: ${value}`}
      data-testid="passport-qr"
      data-url={value}
    >
      <rect width={size} height={size} fill="#fff" />
      {bits.map((on, i) => {
        if (!on) return null;
        const x = (i % cells) * cell;
        const y = Math.floor(i / cells) * cell;
        return <rect key={i} x={x} y={y} width={cell} height={cell} fill="#14201c" />;
      })}
    </svg>
  );
}

export function CareerPassportPage() {
  const { slug = '' } = useParams();
  const query = useQuery({
    queryKey: ['public-passport', slug],
    queryFn: () => publicPassportApi(slug),
    enabled: Boolean(slug),
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
        <div className="brand">LCT Resonance · Career Passport</div>
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
            <p className="muted" style={{ marginBottom: 0, fontSize: '0.85rem' }}>
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
