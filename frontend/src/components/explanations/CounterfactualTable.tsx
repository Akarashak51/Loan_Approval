import type { CounterfactualResult } from '../../types';
import { formatModelFeatureValue } from '../../utils/featureConfig';

export default function CounterfactualTable({ counterfactual }: { counterfactual: CounterfactualResult }) {
  if (!counterfactual.found || counterfactual.alternatives.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 p-4 text-sm text-slate-500">
        {counterfactual.message || 'No alternative profile was found.'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-500 italic">{counterfactual.message}</p>
      {counterfactual.alternatives.map((alt, i) => (
        <div key={i} className="rounded-lg border border-slate-200 overflow-hidden">
          <div className="bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-600">Alternative {i + 1}</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-100">
                <th className="px-3 py-2 font-medium">Feature</th>
                <th className="px-3 py-2 font-medium">Current</th>
                <th className="px-3 py-2 font-medium">Suggested</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(alt).map(([feature, change], j) => (
                <tr key={j} className="border-b border-slate-50 last:border-0">
                  <td className="px-3 py-2 text-slate-700">{change.label}</td>
                  <td className="px-3 py-2 text-rejected">{formatModelFeatureValue(feature, change.current)}</td>
                  <td className="px-3 py-2 text-approved">{formatModelFeatureValue(feature, change.suggested)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  );
}
