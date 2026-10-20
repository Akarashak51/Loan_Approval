type RiskGaugeProps = { score: number; label?: string; change?: number };

export default function RiskGauge({ score, label = 'Risk score', change }: RiskGaugeProps) {
  const safeScore = Math.max(0, Math.min(100, score));
  const circumference = 2 * Math.PI * 44;
  const dashOffset = circumference * (1 - safeScore / 100);
  return <div className="risk-gauge" aria-label={`${label}: ${Math.round(safeScore)} out of 100`}>
    <svg viewBox="0 0 100 100" role="img"><circle className="risk-gauge-track" cx="50" cy="50" r="44" /><circle className="risk-gauge-value" cx="50" cy="50" r="44" strokeDasharray={circumference} strokeDashoffset={dashOffset} /></svg>
    <div className="risk-gauge-center"><strong>{Math.round(safeScore)}</strong><span>{label}</span>{change !== undefined && <em>{change >= 0 ? '+' : ''}{Math.round(change)}%</em>}</div>
  </div>;
}