import api from './api';
import type {
  AttachmentProcessingJob,
  AttachmentProcessingSnapshot,
  MediaProcessingCapability,
  MediaProcessingStatus,
  ProcessedArtifact,
} from '@/types/chat';

interface ApiProcessingJobDTO {
  id: string;
  attachment_id: string;
  capability: MediaProcessingCapability;
  status: MediaProcessingStatus;
  last_error_code?: string | null;
  last_error_message?: string | null;
}

interface ApiProcessingStatusDTO {
  attachment_id: string;
  status: MediaProcessingStatus;
  jobs: ApiProcessingJobDTO[];
}

interface ApiProcessedArtifactDTO {
  id: string;
  attachment_id: string;
  capability: MediaProcessingCapability;
  payload_text?: string | null;
  content_type?: string | null;
  size_bytes?: number | null;
  created_at?: string | null;
}

function mapJob(raw: ApiProcessingJobDTO): AttachmentProcessingJob {
  return {
    id: raw.id,
    attachmentId: raw.attachment_id,
    capability: raw.capability,
    status: raw.status,
    lastErrorCode: raw.last_error_code ?? undefined,
    lastErrorMessage: raw.last_error_message ?? undefined,
  };
}

function mapArtifact(raw: ApiProcessedArtifactDTO): ProcessedArtifact {
  return {
    id: raw.id,
    attachmentId: raw.attachment_id,
    capability: raw.capability,
    payloadText: raw.payload_text ?? undefined,
    contentType: raw.content_type ?? undefined,
    sizeBytes: raw.size_bytes ?? undefined,
    createdAt: raw.created_at ?? undefined,
  };
}

export async function getAttachmentProcessingStatus(attachmentId: string): Promise<AttachmentProcessingSnapshot> {
  const { data } = await api.get<ApiProcessingStatusDTO>(`/attachments/${attachmentId}/status`);
  return {
    attachmentId: data.attachment_id,
    status: data.status,
    jobs: data.jobs.map(mapJob),
  };
}

export async function getAttachmentArtifacts(attachmentId: string): Promise<ProcessedArtifact[]> {
  const { data } = await api.get<ApiProcessedArtifactDTO[]>(`/attachments/${attachmentId}/artifacts`);
  return data.map(mapArtifact);
}
