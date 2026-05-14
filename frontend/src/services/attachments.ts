import api from './api';
import type { Attachment, AttachmentStatus, AttachmentType, MultimediaMessage } from '@/types/chat';
import type { OutboundAttachment } from '@/types/chat';
import type { AxiosProgressEvent } from 'axios';
import axios from 'axios';

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

interface ApiUploadAttachmentResponseDTO {
  provider_url?: string | null;
  providerUrl?: string | null;
  url?: string | null;
  provider_media_id?: string | null;
  providerMediaId?: string | null;
  media_id?: string | null;
  mime_type?: string | null;
  mimeType?: string | null;
  filename?: string | null;
  fileName?: string | null;
  size_bytes?: number | null;
  sizeBytes?: number | null;
  metadata?: Record<string, string | number | boolean | null> | null;
}

interface ApiUploadAttachmentEnvelopeDTO {
  attachment?: ApiUploadAttachmentResponseDTO | null;
  data?: ApiUploadAttachmentResponseDTO | null;
}

function parseUploadResponse(raw: unknown): ApiUploadAttachmentResponseDTO {
  if (!raw || typeof raw !== 'object') {
    throw new Error('Upload response invalid');
  }
  const envelope = raw as ApiUploadAttachmentEnvelopeDTO;
  const candidate = envelope.attachment ?? envelope.data ?? (raw as ApiUploadAttachmentResponseDTO);
  if (!candidate || typeof candidate !== 'object') {
    throw new Error('Upload response missing attachment payload');
  }
  const providerUrl = candidate.provider_url ?? candidate.providerUrl ?? candidate.url ?? null;
  const providerMediaId = candidate.provider_media_id ?? candidate.providerMediaId ?? candidate.media_id ?? null;
  if (!providerUrl && !providerMediaId) {
    throw new Error('Upload response missing provider reference');
  }
  return candidate;
}

function toAttachmentType(value: ApiAttachmentType): AttachmentType {
  return value;
}

function toAttachmentStatus(downloadStatus: ApiDownloadStatus, blobAvailable: boolean): AttachmentStatus {
  if (blobAvailable) return 'available';
  if (downloadStatus === 'failed') return 'failed';
  if (downloadStatus === 'downloading') return 'downloading';
  if (downloadStatus === 'pending' || downloadStatus === 'not_requested') {
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

function toUploadAttachmentType(value: AttachmentType): 'image' | 'audio' | 'video' | 'document' | 'file' {
  return value;
}

export async function uploadAttachmentFile(
  file: File,
  type: AttachmentType,
  options?: {
    signal?: AbortSignal;
    onProgress?: (progress: { loadedBytes: number; totalBytes: number; percent: number }) => void;
  },
): Promise<OutboundAttachment> {
  const form = new FormData();
  form.append('file', file);
  form.append('attachment_type', toUploadAttachmentType(type));

  const endpoint = process.env.NEXT_PUBLIC_ATTACHMENTS_UPLOAD_PATH || '/attachments/upload';
  try {
    const { data } = await api.post<unknown>(endpoint, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      signal: options?.signal,
      timeout: 60000,
      onUploadProgress: (event: AxiosProgressEvent) => {
        const total = event.total ?? file.size;
        const loaded = event.loaded ?? 0;
        const percent = total > 0 ? Math.min(100, Math.round((loaded / total) * 100)) : 0;
        options?.onProgress?.({ loadedBytes: loaded, totalBytes: total, percent });
      },
    });
    const payload = parseUploadResponse(data);
    const providerUrl = payload.provider_url ?? payload.providerUrl ?? payload.url ?? undefined;
    const providerMediaId = payload.provider_media_id ?? payload.providerMediaId ?? payload.media_id ?? undefined;

    return {
      type,
      provider_url: providerUrl ?? undefined,
      provider_media_id: providerMediaId ?? undefined,
      mime_type: payload.mime_type ?? payload.mimeType ?? (file.type || undefined),
      filename: payload.filename ?? payload.fileName ?? file.name,
      size_bytes: payload.size_bytes ?? payload.sizeBytes ?? file.size,
      metadata: payload.metadata ?? undefined,
    };
  } catch (error: unknown) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === 'string') {
        throw new Error(detail);
      }
    }
    throw error;
  }
}
