interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
}

export default function StatCard({ title, value, subtitle }: StatCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md">
      <p className="text-sm font-medium text-slate-600">{title}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
      {subtitle ? <p className="mt-2 text-sm text-slate-500">{subtitle}</p> : null}
    </article>
  );
}
