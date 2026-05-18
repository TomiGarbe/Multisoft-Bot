import { AlertCircle, Check, Mic, Square, Trash2, X } from 'lucide-react';
import { useAudioRecorder } from '@/hooks/useAudioRecorder';
import { formatBytes } from '@/utils/multimedia';

interface Props {
  onRecorded: (file: File, durationMs: number) => void;
  onClose: () => void;
}

export default function AudioRecorder({ onRecorded, onClose }: Props) {
  const {
    status,
    formattedDuration,
    durationMs,
    error,
    audioFile,
    previewUrl,
    startRecording,
    stopRecording,
    cancelRecording,
    clearError,
    clearPreview,
  } = useAudioRecorder();

  const handleStart = () => void startRecording();
  const handleStop = async () => {
    const file = await stopRecording();
    if (file) onRecorded(file, durationMs);
  };

  const isRecording = status === 'recording';
  const isReady = status === 'ready' && !!audioFile && !!previewUrl;

  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-3 shadow-sm">
      <div className="mb-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
          <span
            className={`flex h-7 w-7 items-center justify-center rounded-lg ${
              isRecording
                ? 'bg-rose-100 text-rose-600'
                : 'bg-sky-100 text-sky-600'
            }`}
          >
            <Mic className="h-4 w-4" />
          </span>
          Grabador de audio
        </div>
        <button
          type="button"
          onClick={() => {
            cancelRecording();
            onClose();
          }}
          className="rounded-md p-1 text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-800"
          aria-label="Cerrar grabador"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {error ? (
        <div className="mb-2 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p>{error.message}</p>
            <button
              type="button"
              onClick={clearError}
              className="mt-1 font-medium underline underline-offset-2"
            >
              Cerrar error
            </button>
          </div>
        </div>
      ) : null}

      {!isReady ? (
        <div className="mb-2 flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs">
          <span
            className={`inline-flex items-center gap-1.5 font-medium ${
              isRecording ? 'text-rose-600' : 'text-slate-600'
            }`}
          >
            {isRecording ? (
              <span className="relative inline-flex h-2 w-2">
                <span className="absolute inset-0 animate-ping rounded-full bg-rose-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-rose-500" />
              </span>
            ) : (
              <span className="h-2 w-2 rounded-full bg-slate-300" />
            )}
            {isRecording ? 'Grabando...' : 'Listo para grabar'}
          </span>
          <span className="font-mono text-slate-700">{formattedDuration}</span>
        </div>
      ) : null}

      {isReady ? (
        <div className="mb-2 rounded-xl border border-slate-200 bg-white p-2">
          <audio controls className="w-full">
            <source src={previewUrl} type={audioFile.type || undefined} />
          </audio>
          <p className="mt-1 truncate text-xs text-slate-600">
            {audioFile.name} · {formatBytes(audioFile.size)} · {formattedDuration}
          </p>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        {!isRecording ? (
          <button
            type="button"
            onClick={handleStart}
            className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-all duration-150 hover:bg-sky-700 active:scale-95"
          >
            <Mic className="h-3.5 w-3.5" />
            Grabar
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void handleStop()}
            className="inline-flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition-all duration-150 hover:bg-slate-800 active:scale-95"
          >
            <Square className="h-3.5 w-3.5" />
            Detener
          </button>
        )}

        <button
          type="button"
          onClick={cancelRecording}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-all duration-150 hover:bg-slate-50 active:scale-95"
        >
          <X className="h-3.5 w-3.5" />
          Cancelar
        </button>

        {isReady ? (
          <>
            <button
              type="button"
              onClick={clearPreview}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition-all duration-150 hover:bg-slate-50 active:scale-95"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Regrabar
            </button>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
              <Check className="h-3 w-3" />
              Vista previa lista
            </span>
          </>
        ) : null}
      </div>
    </div>
  );
}
