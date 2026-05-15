import { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import type { Attachment } from '@/types/chat';
import AttachmentStatusHint from './AttachmentStatusHint';
import { useAuthenticatedAttachmentStream } from '@/hooks/useAuthenticatedAttachmentStream';

export default function ImageAttachment({ attachment }: { attachment: Attachment }) {
  const enabled = attachment.status === 'available';
  const { url, loading, error } = useAuthenticatedAttachmentStream(attachment.id, enabled, attachment.streamUrl);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  if (attachment.status !== 'available') return <AttachmentStatusHint attachment={attachment} />;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="group relative overflow-hidden rounded-2xl text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        aria-label="Ampliar imagen"
      >
        {loading ? (
          <div className="h-48 w-64 animate-pulse rounded-2xl bg-gray-200" />
        ) : null}
        {error || !url ? (
          <div className="flex h-40 w-64 items-center justify-center rounded-2xl bg-red-50 text-xs text-red-700">
            Imagen no disponible
          </div>
        ) : (
          <img
            src={url}
            alt={attachment.filename ?? 'Imagen adjunta'}
            className="max-h-72 w-full max-w-sm rounded-2xl object-cover shadow-sm transition group-hover:opacity-90"
            loading="lazy"
          />
        )}
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4"
          role="dialog"
          aria-modal="true"
          onClick={() => setOpen(false)}
        >
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="absolute right-4 top-4 rounded bg-white/10 p-2 text-white hover:bg-white/20"
            aria-label="Cerrar imagen ampliada"
          >
            <X className="h-5 w-5" />
          </button>
          <img
            src={url ?? ''}
            alt={attachment.filename ?? 'Imagen ampliada'}
            className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain"
          />
        </div>
      ) : null}
    </>
  );
}
