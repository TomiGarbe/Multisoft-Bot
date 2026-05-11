interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6">
      <h3 className="text-base font-semibold text-rose-800">No se pudo cargar el dashboard</h3>
      <p className="mt-2 text-sm text-rose-700">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 inline-flex items-center rounded-md bg-rose-600 px-3 py-2 text-sm font-medium text-white hover:bg-rose-700"
      >
        Reintentar
      </button>
    </div>
  );
}
