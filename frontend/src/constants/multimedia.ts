import type { AttachmentType } from '@/types/chat';

const DEFAULT_MAX_ATTACHMENT_MB = 25;

function resolveMaxAttachmentBytes(): number {
  const raw = process.env.NEXT_PUBLIC_MAX_ATTACHMENT_MB;
  const parsed = raw ? Number(raw) : DEFAULT_MAX_ATTACHMENT_MB;
  if (!Number.isFinite(parsed) || parsed <= 0) return DEFAULT_MAX_ATTACHMENT_MB * 1024 * 1024;
  return Math.floor(parsed * 1024 * 1024);
}

export const MAX_ATTACHMENT_SIZE_BYTES = resolveMaxAttachmentBytes();

export const MULTIMEDIA_ACCEPT = [
  'image/*',
  'audio/*',
  'video/*',
  '.pdf',
  '.doc',
  '.docx',
  '.xls',
  '.xlsx',
  '.zip',
  '.txt',
  '.csv',
  '.json',
  '.xml',
  '.ppt',
  '.pptx',
].join(',');

export const ALLOWED_MIME_PREFIXES = ['image/', 'audio/', 'video/'] as const;

export const ALLOWED_MIME_EXACT = new Set<string>([
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'application/vnd.ms-excel',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/zip',
  'text/plain',
  'text/csv',
  'application/json',
  'application/xml',
  'text/xml',
  'application/vnd.ms-powerpoint',
  'application/vnd.openxmlformats-officedocument.presentationml.presentation',
]);

export const ALLOWED_EXTENSIONS = new Set<string>([
  'jpg',
  'jpeg',
  'png',
  'gif',
  'webp',
  'bmp',
  'svg',
  'mp3',
  'wav',
  'ogg',
  'm4a',
  'aac',
  'webm',
  'mp4',
  'mov',
  'avi',
  'mkv',
  'pdf',
  'doc',
  'docx',
  'xls',
  'xlsx',
  'zip',
  'txt',
  'csv',
  'json',
  'xml',
  'ppt',
  'pptx',
]);

export function resolveAttachmentTypeByFile(file: File): AttachmentType {
  const mime = file.type.toLowerCase();
  if (mime.startsWith('image/')) return 'image';
  if (mime.startsWith('audio/')) return 'audio';
  if (mime.startsWith('video/')) return 'video';
  if (mime === 'application/pdf') return 'document';
  return 'file';
}
