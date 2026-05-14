import { FileArchive, FileAudio, FileImage, FileText, FileVideo, FileWarning } from 'lucide-react';
import type { Attachment } from '@/types/chat';
import { formatBytes } from '@/utils/multimedia';

export { formatBytes };

export function formatMediaTime(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function getDocumentIcon(attachment: Attachment) {
  const mime = attachment.mimeType?.toLowerCase() ?? '';
  if (attachment.type === 'image') return FileImage;
  if (attachment.type === 'audio') return FileAudio;
  if (attachment.type === 'video') return FileVideo;
  if (mime.includes('pdf') || mime.includes('text')) return FileText;
  if (mime.includes('zip') || mime.includes('rar')) return FileArchive;
  return FileWarning;
}

export function resolveStatusLabel(status: Attachment['status']): string {
  if (status === 'loading') return 'Cargando multimedia';
  if (status === 'processing') return 'Procesando multimedia';
  if (status === 'downloading') return 'Descargando multimedia';
  if (status === 'failed') return 'Multimedia con error';
  if (status === 'unavailable') return 'Multimedia no disponible';
  return 'Multimedia disponible';
}
