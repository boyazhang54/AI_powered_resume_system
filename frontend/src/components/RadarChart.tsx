import type { RadarScore } from '../types';

interface Props {
  data: RadarScore[];
}

export function RadarChart({ data }: Props) {
  const size = 320;
  const center = size / 2;
  const maxRadius = 108;
  const points = data.map((item, index) => {
    const angle = -Math.PI / 2 + (index * 2 * Math.PI) / data.length;
    const radius = (item.value / 100) * maxRadius;
    return {
      ...item,
      x: center + Math.cos(angle) * radius,
      y: center + Math.sin(angle) * radius,
      lx: center + Math.cos(angle) * (maxRadius + 32),
      ly: center + Math.sin(angle) * (maxRadius + 32),
      ax: center + Math.cos(angle) * maxRadius,
      ay: center + Math.sin(angle) * maxRadius,
    };
  });
  const polygon = points.map((point) => `${point.x},${point.y}`).join(' ');

  return (
    <div className="radar-wrap">
      <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label="多维度雷达图">
        {[0.25, 0.5, 0.75, 1].map((ratio) => {
          const ring = data.map((_, index) => {
            const angle = -Math.PI / 2 + (index * 2 * Math.PI) / data.length;
            const radius = ratio * maxRadius;
            return `${center + Math.cos(angle) * radius},${center + Math.sin(angle) * radius}`;
          });
          return <polygon key={ratio} points={ring.join(' ')} className="radar-ring" />;
        })}
        {points.map((point) => (
          <line key={point.label} x1={center} y1={center} x2={point.ax} y2={point.ay} className="radar-axis" />
        ))}
        <polygon points={polygon} className="radar-area" />
        {points.map((point) => (
          <g key={point.label}>
            <circle cx={point.x} cy={point.y} r="4" className="radar-dot" />
            <text x={point.lx} y={point.ly} textAnchor="middle" dominantBaseline="middle" className="radar-label">
              {point.label}
            </text>
            <text x={point.lx} y={point.ly + 16} textAnchor="middle" dominantBaseline="middle" className="radar-value">
              {point.value}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
