import api from './api';
import type { Attachment, AttachmentStatus, AttachmentType, MultimediaMessage } from '@/types/chat';

type ApiAttachmentType = 'audio' | 'image' | 'video' | 'document' | 'file';
type ApiDownloadStatus =
  | 'not_requested'
  | 'pending'
  | 'downloading'
  | 'completed'
  | 'downloaded'
  | 'failed';

interface ApiAttachmentMetadata {
  id: string;
  message_id: string;
  attachment_type: ApiAttachmentType;
  mime_type: string | null;
  filename: string | null;
  extension: string | null;
  size_bytes: number | null;
  width: number | null;
  height: number | null;
  duration_ms: number | null;
  caption: string | null;
  download_status: ApiDownloadStatus;
}

interface ApiAttachmentDTO {
  metadata: ApiAttachmentMetadata;
  blob_available: boolean;
}

interface ApiMultimediaMessageDTO {
  message_id: string;
  attachments: ApiAttachmentDTO[];
}

function toAttachmentType(value: ApiAttachmentType): AttachmentType {
  return value;
}

function toAttachmentStatus(downloadStatus: ApiDownloadStatus, blobAvailable: boolean): AttachmentStatus {
  if (blobAvailable) return 'available';
  if (downloadStatus === 'failed') return 'failed';
  if (downloadStatus === 'pending' || downloadStatus === 'downloading' || downloadStatus === 'not_requested') {
    return 'processing';
  }
  return 'unavailable';
}

export function getAttachmentStreamUrl(attachmentId: string): string {
  return `${api.defaults.baseURL}/attachments/${attachmentId}/stream`;
}

export function getAttachmentDownloadUrl(attachmentId: string): string {
  return `${api.defaults.baseURL}/attachments/${attachmentId}/download`;
}

function mapAttachment(raw: ApiAttachmentDTO): Attachment {
  return {
    id: raw.metadata.id,
    messageId: raw.metadata.message_id,
    type: toAttachmentType(raw.metadata.attachment_type),
    status: toAttachmentStatus(raw.metadata.download_status, raw.blob_available),
    mimeType: raw.metadata.mime_type ?? undefined,
    filename: raw.metadata.filename ?? undefined,
    extension: raw.metadata.extension ?? undefined,
    sizeBytes: raw.metadata.size_bytes ?? undefined,
    width: raw.metadata.width ?? undefined,
    height: raw.metadata.height ?? undefined,
    durationMs: raw.metadata.duration_ms ?? undefined,
    caption: raw.metadata.caption ?? undefined,
    streamUrl: raw.blob_available ? getAttachmentStreamUrl(raw.metadata.id) : undefined,
    downloadUrl: getAttachmentDownloadUrl(raw.metadata.id),
  };
}

export async function getAttachmentsByMessageId(messageId: string): Promise<MultimediaMessage> {
  const { data } = await api.get<ApiMultimediaMessageDTO>(`/attachments/message/${messageId}`);
  return {
    messageId: data.message_id,
    attachments: data.attachments.map(mapAttachment),
  };
}

