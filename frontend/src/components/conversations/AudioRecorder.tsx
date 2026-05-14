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
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-800">
          <Mic className="h-4 w-4" />
          Grabador de audio
        </div>
        <button
          type="button"
          onClick={() => {
            cancelRecording();
            onClose();
          }}
          className="rounded p-1 text-gray-500 hover:bg-gray-200"
          aria-label="Cerrar grabador"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {error ? (
        <div className="mb-2 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-2 text-xs text-red-700">
          <AlertCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          <div className="min-w-0 flex-1">
            <p>{error.message}</p>
            <button type="button" onClick={clearError} className="mt-1 underline">
              Cerrar error
            </button>
          </div>
        </div>
      ) : null}

      {!isReady ? (
        <div className="mb-2 rounded-lg border border-gray-200 bg-white p-2 text-xs text-gray-700">
          <div className="flex items-center justify-between">
            <span className={isRecording ? 'text-red-600' : 'text-gray-600'}>
              {isRecording ? 'Grabando...' : 'Listo para grabar'}
            </span>
            <span className="font-mono">{formattedDuration}</span>
          </div>
        </div>
      ) : null}

      {isReady ? (
        <div className="mb-2 rounded-lg border border-gray-200 bg-white p-2">
          <audio controls className="w-full">
            <source src={previewUrl} type={audioFile.type || undefined} />
          </audio>
          <p className="mt-1 truncate text-xs text-gray-600">
            {audioFile.name} - {formatBytes(audioFile.size)} - {formattedDuration}
          </p>
        </div>
      ) : null}

      <div className="flex items-center gap-2">
        {!isRecording ? (
          <button
            type="button"
            onClick={handleStart}
            className="inline-flex items-center gap-1 rounded-lg bg-red-600 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-red-700"
          >
            <Mic className="h-3.5 w-3.5" />
            Grabar
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void handleStop()}
            className="inline-flex items-center gap-1 rounded-lg bg-gray-900 px-2.5 py-1.5 text-xs font-medium text-white hover:bg-black"
          >
            <Square className="h-3.5 w-3.5" />
            Detener
          </button>
        )}

        <button
          type="button"
          onClick={cancelRecording}
          className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100"
        >
          <X className="h-3.5 w-3.5" />
          Cancelar
        </button>

        {isReady ? (
          <>
            <button
              type="button"
              onClick={clearPreview}
              className="inline-flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-100"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Regrabar
            </button>
            <span className="inline-flex items-center gap-1 text-xs text-emerald-700">
              <Check className="h-3.5 w-3.5" />
              Vista previa lista
            </span>
          </>
        ) : null}
      </div>
    </div>
  );
}
