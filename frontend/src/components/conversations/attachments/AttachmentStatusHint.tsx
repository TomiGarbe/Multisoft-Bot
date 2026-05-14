import { AlertCircle } from 'lucide-react';
import type { Attachment } from '@/types/chat';

export default function AttachmentStatusHint({ attachment }: { attachment: Attachment }) {
  if (attachment.status === 'processing' || attachment.status === 'loading' || attachment.status === 'downloading') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
        <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border border-current border-t-transparent" />
        Procesando archivo multimedia...
      </div>
    );
  }
  if (attachment.status === 'failed') {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
        <AlertCircle className="h-3.5 w-3.5" />
        Archivo no disponible (fallo)
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
