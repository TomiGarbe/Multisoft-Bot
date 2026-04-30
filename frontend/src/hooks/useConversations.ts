import { useCallback, useEffect, useState } from 'react';
import type { Conversation, Message, SendPayload } from '@/types/chat';
import {
  getConversations,
  getMessages,
  sendMessage,
  setConversationMode,
} from '@/services/conversations';
import { getApiErrorMessage } from '@/services/api';

const POLL_INTERVAL_MS = 8_000;

// Merge fresh server messages with any in-flight (pending/error) local messages.
// Prevents pending messages from disappearing during a background poll.
function mergeWithInFlight(fresh: Message[], prev: Message[]): Message[] {
  const inFlight = prev.filter((m) => m.status === 'pending' || m.status === 'error');
  return [...fresh, ...inFlight];
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [messages, setMessages] = useState<Record<string, Message[]>>({});
  const [loadingConversations, setLoadingConversations] = useState(false);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ─── Reusable fetch helpers ───────────────────────────────────────────────────

  const refreshConversations = useCallback(async (silent = false) => {
    if (!silent) setLoadingConversations(true);
    try {
      const data = await getConversations();
      setConversations(data);
      return data;
    } catch (err: unknown) {
      if (!silent) setError(getApiErrorMessage(err, 'Error al cargar conversaciones'));
      return null;
    } finally {
      if (!silent) setLoadingConversations(false);
    }
  }, []);

  const refreshMessages = useCallback(async (conversationId: string, silent = false) => {
    if (!silent) setLoadingMessages(true);
    try {
      const data = await getMessages(conversationId);
      setMessages((prev) => ({
        ...prev,
        [conversationId]: silent
          ? mergeWithInFlight(data, prev[conversationId] ?? [])
          : data,
      }));
      return data;
    } catch (err: unknown) {
      if (!silent) setError(getApiErrorMessage(err, 'Error al cargar mensajes'));
      return null;
    } finally {
      if (!silent) setLoadingMessages(false);
    }
  }, []);

  // ─── Initial load ─────────────────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false;
    setLoadingConversations(true);

    getConversations()
      .then((data) => {
        if (cancelled) return;
        setConversations(data);
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

  // ─── Fetch messages whenever selected conversation changes (always fresh) ─────

  useEffect(() => {
    if (!selectedId) return;
    let cancelled = false;
    setLoadingMessages(true);

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

  // ─── Background polling: keep messages + sidebar in sync ─────────────────────

  useEffect(() => {
    if (!selectedId) return;

    const tick = () => {
      getMessages(selectedId)
        .then((data) =>
          setMessages((prev) => ({
            ...prev,
            [selectedId]: mergeWithInFlight(data, prev[selectedId] ?? []),
          })),
        )
        .catch(() => {});

      getConversations()
        .then((data) => setConversations(data))
        .catch(() => {});
    };

    const id = setInterval(tick, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [selectedId]);

  // ─── Actions ─────────────────────────────────────────────────────────────────

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

      // 1. Optimistic: add message + update sidebar immediately
      setMessages((prev) => ({
        ...prev,
        [selectedId]: [...(prev[selectedId] ?? []), optimistic],
      }));
      setConversations((prev) =>
        [...prev]
          .map((c) =>
            c.id === selectedId
              ? { ...c, lastMessage: trimmed, lastMessageAt: now }
              : c,
          )
          .sort((a, b) => {
            const at = a.lastMessageAt ? new Date(a.lastMessageAt).getTime() : 0;
            const bt = b.lastMessageAt ? new Date(b.lastMessageAt).getTime() : 0;
            return bt - at;
          }),
      );

      try {
        const saved = await sendMessage({
          conversation_id: selectedId,
          content: trimmed,
        });

        // 2. Replace temp entry with server-confirmed message
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === tempId ? { ...saved, status: 'sent' as const } : m,
          ),
        }));

        // 3. Refetch to catch bot replies and get authoritative ordering
        const [freshMessages] = await Promise.allSettled([
          refreshMessages(selectedId, true),
          refreshConversations(true),
        ]);

        if (freshMessages.status === 'fulfilled' && freshMessages.value) {
          setMessages((prev) => ({ ...prev, [selectedId]: freshMessages.value! }));
        }
      } catch (err: unknown) {
        // Mark as error so user sees what failed (and can retry)
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === tempId ? { ...m, status: 'error' as const } : m,
          ),
        }));
        setError(getApiErrorMessage(err, 'Error al enviar mensaje'));
      }
    },
    [selectedId, refreshMessages, refreshConversations],
  );

  const retryMessage = useCallback(
    async (messageId: string) => {
      if (!selectedId) return;
      const msg = messages[selectedId]?.find((m) => m.id === messageId);
      if (!msg || msg.status !== 'error') return;

      // Reset to pending and retry
      setMessages((prev) => ({
        ...prev,
        [selectedId]: (prev[selectedId] ?? []).map((m) =>
          m.id === messageId ? { ...m, status: 'pending' as const } : m,
        ),
      }));

      try {
        const saved = await sendMessage({
          conversation_id: selectedId,
          content: msg.content,
        });
        setMessages((prev) => ({
          ...prev,
          [selectedId]: (prev[selectedId] ?? []).map((m) =>
            m.id === messageId ? { ...saved, status: 'sent' as const } : m,
          ),
        }));
        await Promise.allSettled([
          refreshMessages(selectedId, true),
          refreshConversations(true),
        ]);
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
    [selectedId, messages, refreshMessages, refreshConversations],
  );

  const toggleMode = useCallback(
    async (conversationId: string, mode: 'ai' | 'human') => {
      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, mode } : c)),
      );
      try {
        await setConversationMode(conversationId, mode);
      } catch (err: unknown) {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? { ...c, mode: mode === 'ai' ? 'human' : 'ai' }
              : c,
          ),
        );
        setError(getApiErrorMessage(err, 'Error al cambiar modo'));
      }
    },
    [],
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
    selectConversation,
    handleSend,
    retryMessage,
    toggleMode,
    dismissError,
  };
}
