export function StatusBadge({ value }: { value: string }) {
  const styles: Record<string, string> = { APPROVE: 'bg-emerald-100 text-emerald-700', APPROVED: 'bg-emerald-100 text-emerald-700', Completed: 'bg-emerald-100 text-emerald-700', REVIEW: 'bg-amber-100 text-amber-700', REJECTED: 'bg-red-100 text-red-700', DECLINE: 'bg-red-100 text-red-700', 'Under Review': 'bg-amber-100 text-amber-700', LOW: 'bg-emerald-100 text-emerald-700', MEDIUM: 'bg-amber-100 text-amber-700', HIGH: 'bg-red-100 text-red-700' };
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${styles[value] ?? 'bg-slate-100 text-slate-600'}`}>{value.replace('_', ' ')}</span>;
}
