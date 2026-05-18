import api from './api';
import type { Conversation, Message, OutboundAttachment } from '@/types/chat';

// ─── Backend raw shapes ────────────────────────────────────────────────────────

interface ApiConversation {
  contact_id: string;
  contact_name?: string | null;
  contact_phone?: string | null;
  contact_current_type?: string | null;
  active_conversation_id?: string | null;
  active_conversation_status?: 'open' | 'closed' | null;
  active_conversation_mode?: 'ai' | 'human' | null;
  channel_id?: string | null;
  channel_name?: string | null;
  channel_type?: string | null;
  channel_provider?: string | null;
  channel_config_id?: string | null;
  last_message_at?: string | null;
  last_message?: string | null;
  unread_count?: number | null;
}

interface ApiMessage {
  id: string;
  conversation_id: string;
  direction: 'inbound' | 'outbound';
  sender_type: 'contact' | 'bot';
  message_type?: string;
  content: string | null;
  has_media?: boolean;
  created_at: string;
  conversation_started_at?: string | null;
  conversation_type?: string | null;
  conversation_status?: string | null;
  is_new_conversation_boundary?: boolean;
}

export interface SendMessagePayload {
  conversation_id: string;
  content: string;
  attachments?: OutboundAttachment[];
}

// ─── Mappers ───────────────────────────────────────────────────────────────────

function mapConversation(raw: ApiConversation): Conversation {
  const normalizedContactType = raw.contact_current_type === 'default' ? 'nuevo' : raw.contact_current_type;
  return {
    id: raw.contact_id,
    contactId: raw.contact_id,
    activeConversationId: raw.active_conversation_id ?? undefined,
    channelId: raw.channel_id ?? undefined,
    channelName: raw.channel_name ?? undefined,
    channelType: raw.channel_type ?? undefined,
    channelProvider: raw.channel_provider ?? undefined,
    channelConfigId: raw.channel_config_id ?? undefined,
    // contactName and contactPhone are not yet returned by GET /conversations.
    // Use a neutral fallback to avoid exposing internal ids in UI.
    contactName: raw.contact_name ?? 'Contacto sin nombre',
    contactPhone: raw.contact_phone ?? undefined,
    contactCurrentType: normalizedContactType ?? undefined,
    status: raw.active_conversation_status ?? 'closed',
    mode: raw.active_conversation_mode ?? 'ai',
    lastMessage: raw.last_message ?? undefined,
    lastMessageAt: raw.last_message_at ?? undefined,
    unreadCount: typeof raw.unread_count === 'number' ? raw.unread_count : 0,
  };
}

function mapMessage(raw: ApiMessage): Message {
  return {
    id: raw.id,
    conversationId: raw.conversation_id,
    direction: raw.direction,
    senderType: raw.sender_type,
    messageType: raw.message_type,
    content: raw.content ?? '',
    hasMedia: Boolean(raw.has_media),
    createdAt: raw.created_at,
    conversationStartedAt: raw.conversation_started_at ?? undefined,
    conversationType: raw.conversation_type ?? undefined,
    conversationStatus: raw.conversation_status ?? undefined,
    isNewConversationBoundary: Boolean(raw.is_new_conversation_boundary),
  };
}

// ─── Service functions ─────────────────────────────────────────────────────────

export async function getConversations(): Promise<Conversation[]> {
  const { data } = await api.get<ApiConversation[]>('/conversations/contacts');
  return data.map(mapConversation);
}

export async function getMessages(contactId: string): Promise<Message[]> {
  const { data } = await api.get<ApiMessage[]>(`/messages/contacts/${contactId}`);
  return data.map(mapMessage);
}

export async function sendMessage(payload: SendMessagePayload): Promise<void> {
  await api.post('/messages/send', payload);
}

// Prepared for: PATCH /conversations/:id/mode
export async function setConversationMode(
  conversationId: string,
  mode: 'ai' | 'human',
): Promise<{ id: string; mode: 'ai' | 'human' }> {
  const { data } = await api.patch<{ id: string; mode: 'ai' | 'human' }>(
    `/conversations/${conversationId}/mode`,
    { mode },
  );
  return data;
}

export async function setContactType(contactId: string, typeKey: string): Promise<void> {
  await api.patch(`/conversations/contacts/${contactId}/type`, { type_key: typeKey });
}

