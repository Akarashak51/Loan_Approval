import { formatCurrencyValue } from '../../utils/featureConfig';

export default function PlainEnglishCard({ text }: { text: string }) {
  const lines = text.split('\n').filter(Boolean);
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm text-slate-700">{formatCurrencyValue(lines[0])}</p>
      <ul className="mt-2 space-y-1">
        {lines.slice(1).map((line, i) => (
          <li key={i} className="text-sm text-slate-600 pl-3 border-l-2 border-brand-200">
            {formatCurrencyValue(line.replace(/^-\s*/, ''))}
          </li>
        ))}
      </ul>
    </div>
  );
}
