export type AttachmentType = 'image' | 'audio' | 'video' | 'document' | 'file';

export type AttachmentStatus =
  | 'loading'
  | 'available'
  | 'processing'
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

export interface MultimediaMessage {
  messageId: string;
  attachments: Attachment[];
}

export interface Conversation {
  id: string;
  channelId?: string;
  channelName?: string;
  channelType?: string;
  channelProvider?: string;
  channelConfigId?: string;
  contactName: string;
  contactPhone?: string;
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
  createdAt: string;
  attachments?: Attachment[];
  status?: MessageStatus;
}

export interface SendPayload {
  text: string;
  files: File[];
}
