import { useMemo, useRef, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import type { Attachment } from '@/types/chat';
import AttachmentStatusHint from './AttachmentStatusHint';
import { formatMediaTime } from './attachmentUtils';
import { useAuthenticatedAttachmentStream } from '@/hooks/useAuthenticatedAttachmentStream';
import { useAttachmentProcessing } from '@/hooks/useAttachmentProcessing';

export default function AudioAttachment({ attachment }: { attachment: Attachment }) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isBuffering, setIsBuffering] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  const label = useMemo(() => `${formatMediaTime(currentTime)} / ${formatMediaTime(duration)}`, [currentTime, duration]);
  const { loading, error, status, transcription } = useAttachmentProcessing(attachment);
  const transcriptionJob = useMemo(
    () => status?.jobs.find((job) => job.capability === 'transcription'),
    [status],
  );
  const isTranscriptionProcessing =
    !transcription &&
    (status?.status === 'pending' ||
      status?.status === 'queued' ||
      status?.status === 'processing' ||
      transcriptionJob?.status === 'pending' ||
      transcriptionJob?.status === 'queued' ||
      transcriptionJob?.status === 'processing');
  const isTranscriptionFailed = !transcription && transcriptionJob?.status === 'failed';
  const failedReason = transcriptionJob?.lastErrorCode || transcriptionJob?.lastErrorMessage;

  const { url, loading: streamLoading, error: streamError } = useAuthenticatedAttachmentStream(
    attachment.id,
    attachment.status === 'available',
    attachment.streamUrl,
  );
  if (attachment.status !== 'available') return <AttachmentStatusHint attachment={attachment} />;
  if (!url) {
    if (streamLoading) return <AttachmentStatusHint attachment={attachment} />;
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-[11px] text-red-700">
        {streamError ? 'No se pudo cargar el audio protegido' : 'No se encontró el audio'}
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
      <audio
        ref={audioRef}
        preload="metadata"
        className="hidden"
        onLoadedMetadata={(event) => {
          setDuration(event.currentTarget.duration || 0);
          setIsLoading(false);
        }}
        onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
        onWaiting={() => setIsBuffering(true)}
        onPlaying={() => setIsBuffering(false)}
        onError={() => {
          setIsLoading(false);
          setHasError(true);
        }}
      >
        <source src={url} type={attachment.mimeType ?? undefined} />
      </audio>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => {
            const target = audioRef.current;
            if (!target) return;
            if (target.paused) void target.play();
            else target.pause();
          }}
          className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
          aria-label={isPlaying ? 'Pausar audio' : 'Reproducir audio'}
        >
          {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
        </button>
        <input
          type="range"
          min={0}
          max={duration || 0}
          value={Math.min(currentTime, duration || 0)}
          onChange={(event) => {
            const next = Number(event.currentTarget.value);
            const target = audioRef.current;
            if (!target || !Number.isFinite(next)) return;
            target.currentTime = next;
            setCurrentTime(next);
          }}
          className="h-1.5 w-52 cursor-pointer accent-blue-600"
          aria-label="Progreso de audio"
        />
        <span className="text-[11px] text-gray-600">{label}</span>
      </div>
      {isLoading ? <p className="mt-1 text-[11px] text-gray-500">Cargando audio...</p> : null}
      {isBuffering ? <p className="mt-1 text-[11px] text-amber-600">Cargando audio...</p> : null}
      {streamError || hasError ? <p className="mt-1 text-[11px] text-red-600">No se pudo reproducir el audio</p> : null}
      {isTranscriptionProcessing ? (
        <div className="mt-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Transcribiendo audio...
        </div>
      ) : null}
      {isTranscriptionFailed ? (
        <div className="mt-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          No se pudo transcribir el audio.
          {failedReason ? <span className="ml-1 text-red-600">({failedReason})</span> : null}
        </div>
      ) : null}
      {transcription?.payloadText ? (
        <div className="mt-2 rounded-xl border border-gray-200 bg-gray-50 p-2">
          <p className="mb-1 text-[11px] font-semibold text-gray-700">Transcripcion</p>
          <p className="max-h-44 overflow-y-auto whitespace-pre-wrap text-xs text-gray-700">{transcription.payloadText}</p>
        </div>
      ) : null}
      {error && attachment.status === 'processing' ? (
        <p className="mt-1 text-[11px] text-red-600">No se pudo consultar el estado de transcripcion.</p>
      ) : null}
      {loading && attachment.status === 'processing' ? (
        <p className="mt-1 text-[11px] text-amber-700">Cargando estado de transcripcion...</p>
      ) : null}
    </div>
  );
}
