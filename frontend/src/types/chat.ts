export type MediaType = 'image' | 'audio' | 'file';

export interface MediaItem {
  url: string;
  type: MediaType;
  name: string;
}

export interface Conversation {
  id: string;
  channelId?: string;
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
  content: string;
  createdAt: string;
  media?: MediaItem[];
  status?: MessageStatus;
}

export interface SendPayload {
  text: string;
  files: File[];
}
