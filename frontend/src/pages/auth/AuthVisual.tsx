import fspLogo from '@/assets/fsp-logo.svg';

export function AuthVisual({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <aside className="auth-visual">
      <img
        className="auth-visual-media"
        src="/auth-hero.png"
        alt=""
        decoding="async"
        fetchPriority="high"
      />
      <div className="auth-visual-shade" aria-hidden />
      <div className="auth-visual-inner">
        <div className="auth-logo">
          <img
            src={fspLogo}
            alt="ФСП — Федерация спортивного программирования"
            className="auth-logo-mark"
            width={138}
            height={47}
          />
          <div className="auth-logo-text">
            <strong>FSP Talent</strong>
            <span>Федерация спортивного программирования</span>
          </div>
        </div>
        <div className="auth-visual-copy">
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </div>
    </aside>
  );
}
