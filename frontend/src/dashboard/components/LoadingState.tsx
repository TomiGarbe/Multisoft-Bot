interface LoadingStateProps {
  cards?: number;
}

export default function LoadingState({ cards = 4 }: LoadingStateProps) {
  return (
    <div className="space-y-5" role="status" aria-live="polite">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: cards }).map((_, index) => (
          <div key={index} className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
        ))}
      </div>
      <div className="h-56 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
      <div className="h-48 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="h-72 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
        <div className="h-72 animate-pulse rounded-2xl border border-slate-200 bg-slate-100" />
      </div>
    </div>
  );
}
