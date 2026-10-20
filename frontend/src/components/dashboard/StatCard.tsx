export default function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: 'approved' | 'rejected' | 'default' }) {
  const toneClass = tone === 'approved' ? 'text-approved' : tone === 'rejected' ? 'text-rejected' : 'text-slate-900';
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${toneClass}`}>{value}</p>
    </div>
  );
}
