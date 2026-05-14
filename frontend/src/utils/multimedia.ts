import {
  ALLOWED_EXTENSIONS,
  ALLOWED_MIME_EXACT,
  ALLOWED_MIME_PREFIXES,
  MAX_ATTACHMENT_SIZE_BYTES,
} from '@/constants/multimedia';
import type { UploadError } from '@/types/chat';

function getExtension(filename: string): string {
  const idx = filename.lastIndexOf('.');
  if (idx < 0 || idx === filename.length - 1) return '';
  return filename.slice(idx + 1).toLowerCase();
}

export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** power;
  return `${value.toFixed(value >= 10 || power === 0 ? 0 : 1)} ${units[power]}`;
}

export function validateAttachmentFile(file: File): UploadError | null {
  if (!file || !(file instanceof File)) {
    return { code: 'file_corrupted', message: 'Archivo invalido', retryable: false };
  }
  if (file.size <= 0) {
    return { code: 'file_corrupted', message: 'Archivo vacio o corrupto', retryable: false };
  }
  if (file.size > MAX_ATTACHMENT_SIZE_BYTES) {
    return {
      code: 'size_exceeded',
      message: `Archivo supera limite de ${Math.round(MAX_ATTACHMENT_SIZE_BYTES / (1024 * 1024))}MB`,
      retryable: false,
    };
  }

  const mime = file.type.toLowerCase();
  const extension = getExtension(file.name);
  const mimeAllowed =
    (!!mime && ALLOWED_MIME_PREFIXES.some((prefix) => mime.startsWith(prefix))) ||
    ALLOWED_MIME_EXACT.has(mime);
  const extensionAllowed = !!extension && ALLOWED_EXTENSIONS.has(extension);

  if (!mimeAllowed && !extensionAllowed) {
    return { code: 'mime_invalid', message: 'Tipo de archivo no soportado', retryable: false };
  }
  return null;
}
