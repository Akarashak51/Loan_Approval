export default function RiskGradientBar({ value, label = 'Portfolio risk position' }: { value: number; label?: string }) {
  const position = Math.max(0, Math.min(100, value));
  return <div className="risk-spectrum" aria-label={`${label}: ${Math.round(position)} out of 100`}><div className="risk-spectrum-track"><span className="risk-spectrum-marker" style={{ left: `${position}%` }} /></div><div className="risk-spectrum-labels"><span>Lower risk</span><span>Higher risk</span></div></div>;
}