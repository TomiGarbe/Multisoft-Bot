import { useCallback, useEffect, useState } from 'react';
import type { Conversation, Message, SendPayload } from '@/types/chat';
import {
  getConversations,
  getMessages,
  sendMessage,
  setConversationMode,
} from '@/services/conversations';
import { getApiErrorMessage } from '@/services/api';
import { getChannelConfigStatus } from '@/services/channelConfig';
import type { ChannelConfigValidationStatus } from '@/types/channelConfig';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [togglingModes, setTogglingModes] = useState<Record<string, boolean>>({});
  const [configStatusByConversation, setConfigStatusByConversation] = useState<
    Record<string, ChannelConfigValidationStatus>
  >({});

  const hydrateConfigStatus = useCallback(async (nextConversations: Conversation[]) => {
    const statusEntries = await Promise.all(
      nextConversations.map(async (conversation) => {
        if (!conversation.channelConfigId) {
          return [conversation.id, { is_valid: false, missing_fields: [] }] as const;
        }

        try {
          const status = await getChannelConfigStatus(conversation.channelConfigId);
          return [conversation.id, status] as const;
        } catch {
          return [conversation.id, { is_valid: false, missing_fields: [] }] as const;
        }
      }),
    );

    setConfigStatusByConversation(Object.fromEntries(statusEntries));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoadingConversations(true);

    getConversations()
      .then((data) => {
        if (cancelled) return;
        setConversations(data);
        hydrateConfigStatus(data).catch(() => {});
        if (data.length > 0) setSelectedId(data[0].id);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(getApiErrorMessage(err, 'Error al cargar conversaciones'));
      })
      .finally(() => {
        if (!cancelled) setLoadingConversations(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    setLoadingMessages(true);
    console.log('Fetching messages...', selectedId);

    getMessages(selectedId)
      .then((data) => {
        if (cancelled) return;
        setMessages((prev) => ({ ...prev, [selectedId]: data }));
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

  const selectConversation = useCallback((id: string) => {
    setSelectedId(id);
  }, []);

  const handleSend = useCallback(
    async ({ text, files }: SendPayload) => {
      const trimmed = text.trim();
      if (!trimmed || !selectedId) return;

      const tempId = `temp_${crypto.randomUUID()}`;
      const now = new Date().toISOString();

      const optimistic: Message = {
        id: tempId,
        conversationId: selectedId,
        direction: 'outbound',
        senderType: 'agent',
        content: trimmed,
        createdAt: now,
        status: 'pending',
        ...(files.length > 0
          ? {
              media: files.map((f) => ({
                url: URL.createObjectURL(f),
                type: f.type.startsWith('image/')
                  ? ('image' as const)
                  : f.type.startsWith('audio/')
                  ? ('audio' as const)
                  : ('file' as const),
                name: f.name,
              })),
            }
          : {}),
      };

      setMessages((prev) => ({
        ...prev,
        [selectedId]: [...(prev[selectedId] ?? []), optimistic],
      }));
      setConversations((prev) =>
        [...prev]
          .map((c) => (c.id === selectedId ? { ...c, lastMessage: trimmed, lastMessageAt: now } : c))
          .sort((a, b) => {
            const at = a.lastMessageAt ? new Date(a.lastMessageAt).getTime() : 0;
            const bt = b.lastMessageAt ? new Date(b.lastMessageAt).getTime() : 0;
            return bt - at;
          }),
      );

      try {
        await sendMessage({
          conversation_id: selectedId,
          content: trimmed,
        });

        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === tempId ? { ...m, status: 'sent' as const } : m,
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
    [selectedId],
  );

  const retryMessage = useCallback(
    async (messageId: string) => {
      if (!selectedId) return;
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
          conversation_id: selectedId,
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
    [selectedId, messages],
  );

  const toggleMode = useCallback(
    async (conversationId: string, mode: 'ai' | 'human') => {
      setTogglingModes((prev) => ({ ...prev, [conversationId]: true }));

      const status = configStatusByConversation[conversationId];
      if (mode === 'ai' && status && !status.is_valid) {
        setError('Completa la configuracion del bot para activar la IA');
        setTogglingModes((prev) => ({ ...prev, [conversationId]: false }));
        return;
      }

      try {
        await setConversationMode(conversationId, mode);
        setConversations((prev) => prev.map((conv) => (conv.id === conversationId ? { ...conv, mode } : conv)));
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
    [configStatusByConversation],
  );

  const dismissError = useCallback(() => setError(null), []);

  return {
    conversations,
    selectedId,
    selectedConversation: conversations.find((c) => c.id === selectedId),
    messages,
    loadingConversations,
    loadingMessages,
    error,
    togglingModes,
    configStatusByConversation,
    selectConversation,
    handleSend,
    retryMessage,
    toggleMode,
    dismissError,
  };
}
