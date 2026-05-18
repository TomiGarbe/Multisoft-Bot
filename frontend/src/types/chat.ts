export type AttachmentType = 'image' | 'audio' | 'video' | 'document' | 'file';

export type AttachmentStatus =
  | 'loading'
  | 'available'
  | 'processing'
  | 'downloading'
  | 'unavailable'
  | 'failed';

export interface Attachment {
  id: string;
  messageId: string;
  type: AttachmentType;
  status: AttachmentStatus;
  mimeType?: string;
  filename?: string;
  extension?: string;
  sizeBytes?: number;
  width?: number;
  height?: number;
  durationMs?: number;
  caption?: string;
  streamUrl?: string;
  downloadUrl?: string;
}

export type MediaProcessingCapability =
  | 'transcription'
  | 'metadata_extraction'
  | 'embeddings'
  | 'moderation'
  | 'thumbnails'
  | 'vision'
  | 'document_extraction';

export type MediaProcessingStatus =
  | 'pending'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'partial'
  | 'skipped';

export interface AttachmentProcessingJob {
  id: string;
  attachmentId: string;
  capability: MediaProcessingCapability;
  status: MediaProcessingStatus;
  lastErrorCode?: string;
  lastErrorMessage?: string;
  metadataJson?: Record<string, unknown>;
}

export interface AttachmentProcessingSnapshot {
  attachmentId: string;
  status: MediaProcessingStatus;
  jobs: AttachmentProcessingJob[];
}

export interface ProcessedArtifact {
  id: string;
  attachmentId: string;
  capability: MediaProcessingCapability;
  payloadText?: string;
  payloadJson?: Record<string, unknown>;
  contentType?: string;
  sizeBytes?: number;
  metadataJson?: Record<string, unknown>;
  createdAt?: string;
}

export interface MultimediaMessage {
  messageId: string;
  attachments: Attachment[];
}

export type UploadState = 'pending' | 'uploading' | 'uploaded' | 'failed' | 'canceled';

export interface UploadProgress {
  loadedBytes: number;
  totalBytes: number;
  percent: number;
}

export type UploadErrorCode =
  | 'size_exceeded'
  | 'mime_invalid'
  | 'upload_failed'
  | 'timeout'
  | 'file_corrupted'
  | 'canceled'
  | 'unknown';

export interface UploadError {
  code: UploadErrorCode;
  message: string;
  retryable: boolean;
}

export interface PendingAttachment {
  localId: string;
  file: File;
  type: AttachmentType;
  previewUrl?: string;
  uploadState: UploadState;
  progress?: UploadProgress;
  error?: UploadError;
  durationMs?: number;
  uploaded?: OutboundAttachment;
}

export type AttachmentMetadataValue = string | number | boolean | null;

export interface OutboundAttachment {
  type: AttachmentType;
  provider_url?: string;
  provider_media_id?: string;
  caption?: string;
  mime_type?: string;
  filename?: string;
  size_bytes?: number;
  metadata?: Record<string, AttachmentMetadataValue>;
}

export interface Conversation {
  id: string;
  contactId?: string;
  activeConversationId?: string;
  channelId?: string;
  channelName?: string;
  channelType?: string;
  channelProvider?: string;
  channelConfigId?: string;
  contactName: string;
  contactPhone?: string;
  contactCurrentType?: string;
  status: 'open' | 'closed';
  mode: 'ai' | 'human';
  lastMessage?: string;
  lastMessageAt?: string;
  unreadCount?: number;
}

export type MessageStatus = 'pending' | 'sent' | 'error';

export interface Message {
  id: string;
  conversationId: string;
  direction: 'inbound' | 'outbound';
  senderType: 'contact' | 'bot' | 'agent';
  messageType?: string;
  content: string;
  hasMedia?: boolean;
  createdAt: string;
  attachments?: Attachment[];
  status?: MessageStatus;
  conversationStartedAt?: string;
  conversationType?: 'AI' | 'HUMAN' | string;
  conversationStatus?: string;
  isNewConversationBoundary?: boolean;
}

export interface UserTypeDefinition {
  key: string;
  label: string;
  color: string;
}

export interface SendPayload {
  text: string;
  attachments: OutboundAttachment[];
}
