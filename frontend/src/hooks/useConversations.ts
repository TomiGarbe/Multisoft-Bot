import { useCallback, useEffect, useMemo, useState } from 'react';
import type { Attachment, Conversation, Message, SendPayload } from '@/types/chat';
import {
  getConversations,
  getMessages,
  sendMessage,
  setConversationMode,
} from '@/services/conversations';
import { getChannels } from '@/services/channels';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import api from '@/services/api';
import { getChannelConfigStatus } from '@/services/channelConfig';
import { getAttachmentsByMessageId } from '@/services/attachments';
import { invalidateAttachmentProcessingCache } from '@/hooks/useAttachmentProcessing';
import type { ChannelConfigValidationStatus } from '@/types/channelConfig';
import type { Channel } from '@/types/channel';
import { getChannelMeta } from '@/components/conversations/channelMeta';

const attachmentCache = new Map<string, Attachment[]>();
const attachmentInFlight = new Map<string, Promise<Attachment[]>>();

function shouldFetchAttachments(message: Message): boolean {
  if (message.hasMedia) return true;
  const kind = (message.messageType ?? '').toLowerCase();
  if (
    kind.includes('image') ||
    kind.includes('audio') ||
    kind.includes('video') ||
    kind.includes('document') ||
    kind.includes('file') ||
    kind.includes('media')
  ) {
    return true;
  }
  return message.content.trim().length === 0;
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [channels, setChannels] = useState<Channel[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [togglingModes, setTogglingModes] = useState<Record<string, boolean>>({});
  const [configStatusByConversation, setConfigStatusByConversation] = useState<
    Record<string, ChannelConfigValidationStatus>
  >({});
  const [search, setSearch] = useState('');
  const [selectedChannel, setSelectedChannel] = useState<string>('all');
  const [selectedStatus, setSelectedStatus] = useState<'all' | 'open' | 'closed'>('all');

  const hydrateConfigStatus = useCallback(async (nextConversations: Conversation[]) => {
    const statusEntries = await Promise.all(
      nextConversations.map(async (conversation) => {
        const key = conversation.activeConversationId ?? conversation.id;
        if (!conversation.channelConfigId) {
          return [key, { is_valid: false, missing_fields: [] }] as const;
        }

        try {
          const status = await getChannelConfigStatus(conversation.channelConfigId);
          return [key, status] as const;
        } catch {
          return [key, { is_valid: false, missing_fields: [] }] as const;
        }
      }),
    );

    setConfigStatusByConversation(Object.fromEntries(statusEntries));
  }, []);

  const channelById = useMemo(() => {
    const entries = channels.map((channel) => [channel.id, channel] as const);
    return Object.fromEntries(entries) as Record<string, Channel>;
  }, [channels]);

  const filteredConversations = useMemo(() => {
    const query = search.trim().toLowerCase();

    return conversations.filter((conversation) => {
      if (selectedStatus !== 'all' && conversation.status !== selectedStatus) return false;

      if (selectedChannel !== 'all' && conversation.channelId !== selectedChannel) return false;

      if (!query) return true;

      const name = conversation.contactName.toLowerCase();
      const phone = (conversation.contactPhone ?? '').toLowerCase();
      const lastMessage = (conversation.lastMessage ?? '').toLowerCase();
      return name.includes(query) || phone.includes(query) || lastMessage.includes(query);
    });
  }, [conversations, search, selectedChannel, selectedStatus]);
  const selectedConversation = useMemo(
    () => filteredConversations.find((c) => c.id === selectedId),
    [filteredConversations, selectedId],
  );
  const activeConversationId = selectedConversation?.activeConversationId;

  const channelOptions = useMemo(() => {
    return channels
      .filter((channel) => channel.is_active)
      .map((channel) => ({ value: channel.id, label: channel.name }))
      .sort((a, b) => a.label.localeCompare(b.label));
  }, [channels]);

  const stats = useMemo(() => {
    const open = filteredConversations.filter((conversation) => conversation.status === 'open').length;
    return {
      total: filteredConversations.length,
      open,
    };
  }, [filteredConversations]);

  const clearFilters = useCallback(() => {
    setSearch('');
    setSelectedChannel('all');
    setSelectedStatus('all');
  }, []);

  const resolveConversationChannel = useCallback(
    (conversation: Conversation) => {
      const mapped = conversation.channelId ? channelById[conversation.channelId] : undefined;
      if (mapped) return getChannelMeta(mapped);
      return getChannelMeta({
        id: conversation.channelId ?? '',
        tenant_id: '',
        type: conversation.channelType ?? 'canal',
        name: conversation.channelName ?? 'Sin canal',
        external_id: '',
        config: conversation.channelProvider
          ? ({ provider: conversation.channelProvider } as unknown as Channel['config'])
          : undefined,
        is_active: true,
      });
    },
    [channelById],
  );

  const loadConversationsData = useCallback(async () => {
    setLoadingConversations(true);

    try {
      const [nextConversations, nextChannels] = await Promise.all([getConversations(), getChannels()]);
      setConversations(nextConversations);
      setChannels(nextChannels);
      await hydrateConfigStatus(nextConversations);
      setSelectedId((currentSelected) => {
        if (!nextConversations.length) return '';
        if (currentSelected && nextConversations.some((conversation) => conversation.id === currentSelected)) {
          return currentSelected;
        }
        return nextConversations[0].id;
      });
    } catch (err: unknown) {
      setError(getApiErrorMessage(err, 'Error al cargar conversaciones'));
    } finally {
      setLoadingConversations(false);
    }
  }, [hydrateConfigStatus]);

  useEffect(() => {
    void loadConversationsData().catch(() => {});
  }, [loadConversationsData]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      attachmentCache.clear();
      attachmentInFlight.clear();
      setConversations([]);
      setSelectedId('');
      setMessages({});
      setConfigStatusByConversation({});
      setError(null);
      setSearch('');
      setSelectedChannel('all');
      setSelectedStatus('all');
      void loadConversationsData().catch(() => {});
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [loadConversationsData]);

  useEffect(() => {
    if (!filteredConversations.length) {
      setSelectedId('');
      return;
    }

    setSelectedId((currentSelected) => {
      if (!currentSelected) return filteredConversations[0].id;
      if (filteredConversations.some((conversation) => conversation.id === currentSelected)) {
        return currentSelected;
      }
      return filteredConversations[0].id;
    });
  }, [filteredConversations]);

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    setLoadingMessages(true);

    getMessages(selectedId)
      .then(async (data) => {
        const attachmentsByMessage = await Promise.allSettled(
          data.map(async (message) => {
            if (!shouldFetchAttachments(message)) {
              return { messageId: message.id, attachments: [] as Attachment[] };
            }
            const cached = attachmentCache.get(message.id);
            if (cached) return { messageId: message.id, attachments: cached };
            const running =
              attachmentInFlight.get(message.id) ??
              getAttachmentsByMessageId(message.id).then((response) => {
                attachmentCache.set(message.id, response.attachments);
                return response.attachments;
              });
            attachmentInFlight.set(message.id, running);
            try {
              const resolved = await running;
              return { messageId: message.id, attachments: resolved };
            } finally {
              attachmentInFlight.delete(message.id);
            }
          }),
        );
        const nextMessages = data.map((message, index) => {
          const resolved = attachmentsByMessage[index];
          if (resolved.status !== 'fulfilled') {
            return message;
          }
          return {
            ...message,
            attachments: resolved.value.attachments,
          };
        });
        if (cancelled) return;
        setMessages((prev) => ({ ...prev, [selectedId]: nextMessages }));
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(getApiErrorMessage(err, 'Error al cargar mensajes'));
      })
      .finally(() => {
        if (!cancelled) setLoadingMessages(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const baseUrl = (api.defaults.baseURL ?? '').replace(/\/$/, '');
    if (!baseUrl) return;
    const token = window.localStorage.getItem('access_token');
    const tenantId = window.localStorage.getItem('active_tenant_id');
    if (!token) return;
    const query = new URLSearchParams({ access_token: token });
    if (tenantId && tenantId.trim().length > 0) {
      query.set('tenant_id', tenantId);
    }
    const source = new EventSource(`${baseUrl}/realtime/events?${query.toString()}`);
    source.addEventListener('attachment_updated', (event) => {
      try {
        const data = JSON.parse((event as MessageEvent).data ?? '{}') as {
          message_id?: string;
          attachment_id?: string;
        };
        const messageId = (data.message_id ?? '').trim();
        const attachmentId = (data.attachment_id ?? '').trim();
        if (!messageId) return;
        if (attachmentId) invalidateAttachmentProcessingCache(attachmentId);
        void getAttachmentsByMessageId(messageId).then((response) => {
          attachmentCache.set(messageId, response.attachments);
          setMessages((prev) => {
            const next = { ...prev };
            for (const [conversationId, list] of Object.entries(next)) {
              next[conversationId] = list.map((msg) =>
                msg.id === messageId ? { ...msg, attachments: response.attachments } : msg,
              );
            }
            return next;
          });
        });
      } catch {
        // Ignore malformed realtime payloads.
      }
    });
    source.addEventListener('new_message', () => {
      void loadConversationsData().catch(() => {});
    });
    source.addEventListener('conversation_opened', () => {
      void loadConversationsData().catch(() => {});
    });
    source.addEventListener('conversation_closed', () => {
      void loadConversationsData().catch(() => {});
    });
    source.addEventListener('conversation_changed', () => {
      void loadConversationsData().catch(() => {});
    });
    return () => source.close();
  }, [loadConversationsData]);

  const selectConversation = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  const handleSend = useCallback(
    async ({ text, attachments }: SendPayload) => {
      const trimmed = text.trim();
      if ((!trimmed && attachments.length === 0) || !selectedId) return;

      if (!activeConversationId) return;

      const tempId = `temp_${crypto.randomUUID()}`;
      const now = new Date().toISOString();

      const optimistic: Message = {
        id: tempId,
        conversationId: activeConversationId,
        direction: 'outbound',
        senderType: 'agent',
        content: trimmed,
        createdAt: now,
        status: 'pending',
        attachments: attachments.map<Attachment>((item, index) => ({
          id: `${tempId}_att_${index}`,
          messageId: tempId,
          type: item.type,
          status: 'processing',
          mimeType: item.mime_type,
          filename: item.filename,
          sizeBytes: item.size_bytes,
        })),
      };

      setMessages((prev) => ({
        ...prev,
        [selectedId]: [...(prev[selectedId] ?? []), optimistic],
      }));
      const lastMessagePreview = trimmed || 'Adjunto multimedia';
      setConversations((prev) =>
        [...prev]
          .map((c) => (c.id === selectedId ? { ...c, lastMessage: lastMessagePreview, lastMessageAt: now } : c))
          .sort((a, b) => {
            const at = a.lastMessageAt ? new Date(a.lastMessageAt).getTime() : 0;
            const bt = b.lastMessageAt ? new Date(b.lastMessageAt).getTime() : 0;
            return bt - at;
          }),
      );

      try {
        await sendMessage({
          conversation_id: activeConversationId,
          content: trimmed,
          attachments,
        });
        const serverMessages = await getMessages(selectedId);
        const knownIds = new Set((messages[selectedId] ?? []).map((item) => item.id));
        const candidate = [...serverMessages]
          .reverse()
          .find((item) => item.direction === 'outbound' && item.content === trimmed && !knownIds.has(item.id));
        if (!candidate) {
          setMessages((prev) => ({
            ...prev,
            [selectedId]: (prev[selectedId] ?? []).map((m) =>
              m.id === tempId ? { ...m, status: 'sent' as const } : m,
            ),
          }));
          return;
        }
        let nextAttachments: Attachment[] = [];
        if (shouldFetchAttachments(candidate)) {
          try {
            const response = await getAttachmentsByMessageId(candidate.id);
            nextAttachments = response.attachments;
            attachmentCache.set(candidate.id, nextAttachments);
          } catch {
            nextAttachments = [];
          }
        }
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === tempId
              ? {
                  ...candidate,
                  attachments: nextAttachments,
                  status: 'sent' as const,
                }
              : m,
          ),
        }));
      } catch (err: unknown) {
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === tempId ? { ...m, status: 'error' as const } : m,
          ),
        }));
        setError(getApiErrorMessage(err, 'Error al enviar mensaje'));
      }
    },
    [selectedId, activeConversationId, messages],
  );

  const retryMessage = useCallback(
    async (messageId: string) => {
      if (!selectedId) return;
      if (!activeConversationId) return;
      const msg = messages[selectedId]?.find((m) => m.id === messageId);
      if (!msg || msg.status !== 'error') return;

      setMessages((prev) => ({
        ...prev,
        [selectedId]: (prev[selectedId] ?? []).map((m) =>
          m.id === messageId ? { ...m, status: 'pending' as const } : m,
        ),
      }));

      try {
        await sendMessage({
          conversation_id: activeConversationId,
          content: msg.content,
        });
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === messageId ? { ...m, status: 'sent' as const } : m,
          ),
        }));
      } catch (err: unknown) {
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === messageId ? { ...m, status: 'error' as const } : m,
          ),
        }));
        setError(getApiErrorMessage(err, 'Error al reenviar mensaje'));
      }
    },
    [selectedId, activeConversationId, messages],
  );

  const toggleMode = useCallback(
    async (_contactId: string, mode: 'ai' | 'human') => {
      const conversationId = activeConversationId;
      if (!conversationId) return;
      setTogglingModes((prev) => ({ ...prev, [conversationId]: true }));

      const status = configStatusByConversation[conversationId];
      if (mode === 'ai' && status && !status.is_valid) {
        setError('Completa la configuracion del bot para activar la IA');
        setTogglingModes((prev) => ({ ...prev, [conversationId]: false }));
        return;
      }

      try {
        await setConversationMode(conversationId, mode);
        await loadConversationsData();
      } catch (err: unknown) {
        const apiMsg = getApiErrorMessage(err, 'Error al cambiar modo');

        if (typeof apiMsg === 'string' && /config|bot|bot_config|configuracion/i.test(apiMsg)) {
          setError('Completa la configuracion del bot para activar la IA');
        } else {
          setError(apiMsg);
        }

      } finally {
        setTogglingModes((prev) => ({ ...prev, [conversationId]: false }));
      }
    },
    [configStatusByConversation, loadConversationsData, activeConversationId],
  );

  const dismissError = useCallback(() => setError(null), []);

  return {
    conversations: filteredConversations,
    allConversations: conversations,
    selectedId,
    selectedConversation,
    messages,
    loadingConversations,
    loadingMessages,
    error,
    togglingModes,
    configStatusByConversation,
    search,
    selectedChannel,
    selectedStatus,
    channelOptions,
    stats,
    selectConversation,
    setSearch,
    setSelectedChannel,
    setSelectedStatus,
    clearFilters,
    resolveConversationChannel,
    handleSend,
    retryMessage,
    toggleMode,
    dismissError,
  };
}
