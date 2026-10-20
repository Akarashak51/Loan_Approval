import type { ComparisonResult } from '../../types';

export default function ComparisonPanel({ comparison }: { comparison: ComparisonResult }) {
  return (
    <div className="space-y-3 text-sm">
      <p className="text-xs text-slate-500 italic">{comparison.note}</p>

      <div>
        <p className="font-medium text-slate-700 mb-1">Agreement ({comparison.agreement.length})</p>
        {comparison.agreement.length === 0 ? (
          <p className="text-slate-400 text-xs">No overlapping top features.</p>
        ) : (
          <ul className="space-y-1">
            {comparison.agreement.map((a) => (
              <li key={a.feature} className="text-slate-600">
                {a.label}: SHAP {a.shap_contribution.toFixed(3)}, LIME {a.lime_contribution.toFixed(3)} (both {a.shap_direction})
              </li>
            ))}
          </ul>
        )}
      </div>

      {comparison.direction_disagreement.length > 0 && (
        <div>
          <p className="font-medium text-slate-700 mb-1">Direction Disagreement ({comparison.direction_disagreement.length})</p>
          <ul className="space-y-1">
            {comparison.direction_disagreement.map((d) => (
              <li key={d.feature} className="text-slate-600">
                {d.label}: SHAP says {d.shap_direction}, LIME says {d.lime_direction}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
