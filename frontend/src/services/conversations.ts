import api from './api';
import type { Conversation, Message } from '@/types/chat';

// ─── Backend raw shapes ────────────────────────────────────────────────────────

interface ApiConversation {
  id: string;
  status: 'open' | 'closed';
  mode?: 'ai' | 'human';
  channel_id?: string | null;
  channel_config_id?: string | null;
  started_at: string;
  last_message_at: string | null;
  chat_thread_id?: string | null;
}

interface ApiMessage {
  id: string;
  conversation_id: string;
  direction: 'inbound' | 'outbound';
  sender_type: 'contact' | 'bot';
  message_type?: string;
  content: string | null;
  created_at: string;
}

export interface SendMessagePayload {
  conversation_id: string;
  content: string;
}

// ─── Mappers ───────────────────────────────────────────────────────────────────

function mapConversation(raw: ApiConversation): Conversation {
  return {
    id: raw.id,
    channelId: raw.channel_id ?? undefined,
    channelConfigId: raw.channel_config_id ?? undefined,
    // contactName and contactPhone are not yet returned by GET /conversations.
    // Fallback until the backend includes contact info in the response.
    contactName: `Contacto ${raw.id.slice(0, 8)}`,
    status: raw.status,
    // mode is part of the backend model but not yet in GET /conversations response.
    mode: raw.mode ?? 'ai',
    lastMessageAt: raw.last_message_at ?? undefined,
  };
}

function mapMessage(raw: ApiMessage): Message {
  return {
    id: raw.id,
    conversationId: raw.conversation_id,
    direction: raw.direction,
    senderType: raw.sender_type,
    content: raw.content ?? '',
    createdAt: raw.created_at,
  };
}

// ─── Service functions ─────────────────────────────────────────────────────────

export async function getConversations(): Promise<Conversation[]> {
  const { data } = await api.get<ApiConversation[]>('/conversations');
  return data.map(mapConversation);
}

export async function getMessages(conversationId: string): Promise<Message[]> {
  const { data } = await api.get<ApiMessage[]>(`/messages/${conversationId}`);
  return data.map(mapMessage);
}

export async function sendMessage(payload: SendMessagePayload): Promise<Message> {
  const { data } = await api.post<ApiMessage>('/messages/send', payload);
  return mapMessage(data);
}

// Prepared for: PATCH /conversations/:id/mode
export async function setConversationMode(
  conversationId: string,
  mode: 'ai' | 'human',
): Promise<void> {
  await api.patch(`/conversations/${conversationId}/mode`, { mode });
}
