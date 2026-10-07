import type { SkillRadar as SkillRadarData } from '@/entities/types';

type Props = {
  radar: SkillRadarData;
  size?: number;
};

/**
 * Pure visualization of Backend/ML SkillRadar DTO.
 * Does not compute scores — only draws provided axes.
 */
export function SkillRadar({ radar, size = 280 }: Props) {
  const axes = radar.axes;
  if (axes.length === 0) {
    return <p className="muted">Нет данных для Skill Radar.</p>;
  }

  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.36;
  const angleStep = (Math.PI * 2) / axes.length;

  const point = (index: number, score: number) => {
    const angle = -Math.PI / 2 + index * angleStep;
    const r = (Math.max(0, Math.min(100, score)) / 100) * radius;
    return {
      x: cx + Math.cos(angle) * r,
      y: cy + Math.sin(angle) * r,
    };
  };

  const polygon = axes
    .map((axis, i) => {
      const p = point(i, axis.score);
      return `${p.x},${p.y}`;
    })
    .join(' ');

  const levels = [0.25, 0.5, 0.75, 1];

  return (
    <div className="section-card" data-testid="skill-radar">
      <h3>Skill Radar</h3>
      <p className="muted" style={{ marginTop: 0 }}>
        Оценки рассчитаны на Backend/ML. Frontend только отображает.
      </p>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        role="img"
        aria-label={`Skill radar для кандидата ${radar.candidateId}`}
      >
        {levels.map((level) => (
          <polygon
            key={level}
            fill="none"
            stroke="rgba(20,32,28,0.12)"
            points={axes
              .map((_, i) => {
                const p = point(i, level * 100);
                return `${p.x},${p.y}`;
              })
              .join(' ')}
          />
        ))}
        {axes.map((axis, i) => {
          const edge = point(i, 100);
          const label = point(i, 118);
          return (
            <g key={axis.skill}>
              <line x1={cx} y1={cy} x2={edge.x} y2={edge.y} stroke="rgba(20,32,28,0.2)" />
              <text
                x={label.x}
                y={label.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="11"
                fill="#14201c"
              >
                {axis.skill} ({axis.score})
              </text>
            </g>
          );
        })}
        <polygon points={polygon} fill="rgba(13,122,95,0.28)" stroke="#0d7a5f" strokeWidth="2" />
      </svg>
    </div>
  );
}
