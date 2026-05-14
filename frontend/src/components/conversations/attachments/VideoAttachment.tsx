import { useState } from 'react';
import type { Attachment } from '@/types/chat';
import AttachmentStatusHint from './AttachmentStatusHint';

export default function VideoAttachment({ attachment }: { attachment: Attachment }) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  if (attachment.status !== 'available' || !attachment.streamUrl) return <AttachmentStatusHint attachment={attachment} />;

  return (
    <div className="overflow-hidden rounded-2xl border border-gray-200 bg-black shadow-sm">
      <video
        controls
        preload="metadata"
        className="max-h-80 w-full max-w-md"
        poster=""
        onLoadStart={() => setIsLoading(true)}
        onLoadedData={() => setIsLoading(false)}
        onError={() => {
          setIsLoading(false);
          setHasError(true);
        }}
      >
        <source src={attachment.streamUrl} type={attachment.mimeType ?? undefined} />
      </video>
      {isLoading ? <p className="px-3 py-1 text-xs text-gray-300">Cargando video...</p> : null}
      {hasError ? <p className="px-3 py-1 text-xs text-red-300">No se pudo reproducir el video</p> : null}
    </div>
  );
}
