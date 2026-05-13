import { AlertCircle, Download, FileText, Play, RotateCcw } from 'lucide-react';
import { useMemo, useState } from 'react';
import type { Attachment, Message } from '@/types/chat';

interface Props {
  message: Message;
  grouped?: boolean;
  onRetry?: (messageId: string) => void;
}

function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatBytes(bytes?: number): string {
  if (!bytes || bytes <= 0) return 'Tamano desconocido';
  const units = ['B', 'KB', 'MB', 'GB'];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function AudioAttachment({ attachment }: { attachment: Attachment }) {
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  if (!attachment.streamUrl) {
    return <AttachmentStatusHint attachment={attachment} />;
  }

  return (
    <div className="rounded-2xl border border-gray-200 bg-white px-3 py-2.5 shadow-sm">
      <audio
        controls
        preload="metadata"
        className="h-8 w-full"
        style={{ minWidth: '240px', maxWidth: '340px' }}
        onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
        onLoadedMetadata={(event) => setDuration(event.currentTarget.duration || 0)}
      >
        <source src={attachment.streamUrl} type={attachment.mimeType ?? undefined} />
      </audio>
      <p className="mt-1 text-[11px] text-gray-500">
        {Math.floor(currentTime)}s / {Math.floor(duration)}s
      </p>
    </div>
  );
}

function AttachmentStatusHint({ attachment }: { attachment: Attachment }) {
  if (attachment.status === 'processing' || attachment.status === 'loading') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
        <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border border-current border-t-transparent" />
        Procesando archivo...
      </div>
    );
  }
  if (attachment.status === 'failed') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
        <AlertCircle className="h-3.5 w-3.5" />
        Archivo no disponible (fallo de descarga)
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2 rounded-xl border border-gray-200 bg-gray-50 px-3 py-2 text-xs text-gray-600">
      <AlertCircle className="h-3.5 w-3.5" />
      Archivo no disponible
    </div>
  );
}

function AttachmentCard({ attachment, createdAt }: { attachment: Attachment; createdAt: string }) {
  const [loadError, setLoadError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const showUnavailable = attachment.status !== 'available' || !attachment.streamUrl;
  if (showUnavailable) return <AttachmentStatusHint attachment={attachment} />;

  if (attachment.type === 'image') {
    return (
      <div className="relative overflow-hidden rounded-2xl shadow-sm">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 text-xs text-gray-500">
            Cargando imagen...
          </div>
        )}
        {loadError ? (
          <div className="flex h-40 w-64 items-center justify-center bg-red-50 text-xs text-red-700">
            Imagen no disponible
          </div>
        ) : (
          <img
            src={attachment.streamUrl}
            alt={attachment.filename ?? 'Imagen'}
            className="max-h-72 w-full max-w-sm object-cover"
            loading="lazy"
            onLoad={() => setIsLoading(false)}
            onError={() => {
              setIsLoading(false);
              setLoadError(true);
            }}
          />
        )}
        <span className="absolute bottom-1.5 right-2 rounded bg-black/30 px-1 text-[10px] text-white select-none">
          {formatTime(createdAt)}
        </span>
      </div>
    );
  }

  if (attachment.type === 'audio') {
    return <AudioAttachment attachment={attachment} />;
  }

  if (attachment.type === 'video') {
    return (
      <div className="rounded-2xl bg-black p-1 shadow-sm">
        <video
          controls
          preload="metadata"
          className="max-h-80 w-full max-w-sm rounded-xl"
          onLoadStart={() => setIsLoading(true)}
          onLoadedData={() => setIsLoading(false)}
          onError={() => {
            setIsLoading(false);
            setLoadError(true);
          }}
        >
          <source src={attachment.streamUrl} type={attachment.mimeType ?? undefined} />
        </video>
        {isLoading && <p className="px-2 py-1 text-xs text-gray-300">Cargando video...</p>}
        {loadError && <p className="px-2 py-1 text-xs text-red-300">Video no disponible</p>}
      </div>
    );
  }

  return (
    <a
      href={attachment.downloadUrl ?? attachment.streamUrl}
      target="_blank"
      rel="noreferrer"
      download={attachment.filename}
      className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-3 py-2.5 text-gray-900 shadow-sm transition-opacity hover:opacity-85"
    >
      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100">
        <FileText className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{attachment.filename ?? 'Archivo'}</p>
        <p className="text-[11px] text-gray-500">{formatBytes(attachment.sizeBytes)}</p>
      </div>
      <Download className="h-4 w-4 flex-shrink-0 opacity-60" />
    </a>
  );
}

export default function ConversationMessage({ message, grouped = false, onRetry }: Props) {
  const isInbound = message.direction === 'inbound';
  const isPending = message.status === 'pending';
  const isError = message.status === 'error';
  const attachments = useMemo(() => message.attachments ?? [], [message.attachments]);

  return (
    <div className={`flex flex-col ${isInbound ? 'items-start' : 'items-end'} ${grouped ? 'mt-0.5' : 'mt-3'}`}>
      <div className="flex max-w-[70%] flex-col gap-1">
        {message.content && (
          <div
            className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed transition-opacity ${
              isPending ? 'opacity-60' : 'opacity-100'
            } ${
              isError
                ? 'rounded-tr-sm border border-red-200 bg-red-50 text-gray-900 shadow-sm'
                : isInbound
                ? 'rounded-tl-sm border border-gray-100 bg-white text-gray-900 shadow-sm'
                : 'rounded-tr-sm bg-blue-500 text-white'
            }`}
          >
            <p className="break-words whitespace-pre-wrap">{message.content}</p>
            <span
              className={`mt-1 flex select-none items-center justify-end gap-1 text-[10px] ${
                isInbound ? 'text-gray-400' : isError ? 'text-red-400' : 'text-blue-200'
              }`}
            >
              {formatTime(message.createdAt)}
              {isPending && (
                <span className="inline-block h-2.5 w-2.5 animate-spin rounded-full border border-current border-t-transparent" />
              )}
              {isError && <AlertCircle className="h-3 w-3 text-red-400" />}
            </span>
          </div>
        )}

        {attachments.map((attachment) => (
          <AttachmentCard key={attachment.id} attachment={attachment} createdAt={message.createdAt} />
        ))}

        {isError && onRetry && (
          <button
            onClick={() => onRetry(message.id)}
            className="self-end text-[11px] text-red-500 transition-colors hover:text-red-700"
          >
            <span className="inline-flex items-center gap-1">
              <RotateCcw className="h-3 w-3" />
              Reintentar
            </span>
          </button>
        )}

        {!message.content && attachments.length === 0 && (
          <div className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs text-gray-500">
            <Play className="h-3.5 w-3.5" />
            Mensaje sin contenido
          </div>
        )}
      </div>
    </div>
  );
}

