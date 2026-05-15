import api from './api';
import type { Conversation, Message, OutboundAttachment } from '@/types/chat';

// ─── Backend raw shapes ────────────────────────────────────────────────────────

interface ApiConversation {
  id: string;
  status: 'open' | 'closed';
  mode?: 'ai' | 'human';
  channel_id?: string | null;
  channel_name?: string | null;
  channel_type?: string | null;
  channel_provider?: string | null;
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
  attachments?: OutboundAttachment[];
}

// ─── Mappers ───────────────────────────────────────────────────────────────────

function mapConversation(raw: ApiConversation): Conversation {
  return {
    id: raw.id,
    channelId: raw.channel_id ?? undefined,
    channelName: raw.channel_name ?? undefined,
    channelType: raw.channel_type ?? undefined,
    channelProvider: raw.channel_provider ?? undefined,
    channelConfigId: raw.channel_config_id ?? undefined,
    // contactName and contactPhone are not yet returned by GET /conversations.
    // Use a neutral fallback to avoid exposing internal ids in UI.
    contactName: 'Contacto sin nombre',
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
    messageType: raw.message_type,
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

export async function sendMessage(payload: SendMessagePayload): Promise<void> {
  console.warn('[MULTIMEDIA][SEND_MESSAGE] request_prepare', {
    conversationId: payload.conversation_id,
    contentLength: payload.content.length,
    attachmentsCount: payload.attachments?.length ?? 0,
    attachments: (payload.attachments ?? []).map((item, index) => ({
      index,
      type: item.type,
      filename: item.filename,
      mimeType: item.mime_type,
      sizeBytes: item.size_bytes,
      providerMediaId: item.provider_media_id,
      hasProviderUrl: Boolean(item.provider_url),
    })),
  });
  await api.post('/messages/send', payload);
  console.warn('[MULTIMEDIA][SEND_MESSAGE] request_success', {
    conversationId: payload.conversation_id,
    attachmentsCount: payload.attachments?.length ?? 0,
  });
}

// Prepared for: PATCH /conversations/:id/mode
export async function setConversationMode(
  conversationId: string,
  mode: 'ai' | 'human',
): Promise<void> {
  await api.patch(`/conversations/${conversationId}/mode`, { mode });
}

