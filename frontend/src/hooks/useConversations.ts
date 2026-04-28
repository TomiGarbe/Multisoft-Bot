import { useEffect, useMemo, useRef, useState } from 'react';

export interface Conversation {
  id: string;
  contactName: string;
  lastMessage: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  createdAt: string;
}

const INITIAL_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-1',
    contactName: 'Juan Perez',
    lastMessage: 'Perfecto, gracias por la ayuda.',
  },
  {
    id: 'conv-2',
    contactName: 'Maria Gomez',
    lastMessage: 'Necesito soporte con mi acceso.',
  },
  {
    id: 'conv-3',
    contactName: 'Carlos Diaz',
    lastMessage: 'Enviame el estado del ticket.',
  },
];

const INITIAL_MESSAGES: Record<string, ChatMessage[]> = {
  'conv-1': [
    {
      id: 'm-1',
      sender: 'bot',
      content: 'Hola Juan, en que puedo ayudarte hoy?',
      createdAt: new Date().toISOString(),
    },
    {
      id: 'm-2',
      sender: 'user',
      content: 'Queria confirmar si mi solicitud fue aprobada.',
      createdAt: new Date().toISOString(),
    },
    {
      id: 'm-3',
      sender: 'bot',
      content: 'Si, la solicitud ya fue aprobada.',
      createdAt: new Date().toISOString(),
    },
  ],
  'conv-2': [
    {
      id: 'm-4',
      sender: 'user',
      content: 'No puedo ingresar al panel.',
      createdAt: new Date().toISOString(),
    },
    {
      id: 'm-5',
      sender: 'bot',
      content: 'Entiendo. Ya verifico tu usuario y te confirmo.',
      createdAt: new Date().toISOString(),
    },
  ],
  'conv-3': [
    {
      id: 'm-6',
      sender: 'user',
      content: 'Tenes novedades del ticket #382?',
      createdAt: new Date().toISOString(),
    },
  ],
};

function buildBotReply(text: string): string {
  return `Recibido: "${text}". Este es un mensaje automatico de prueba.`;
}

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>(INITIAL_CONVERSATIONS);
  const [selectedConversationId, setSelectedConversationId] = useState<string>(INITIAL_CONVERSATIONS[0]?.id ?? '');
  const [messagesByConversation, setMessagesByConversation] = useState<Record<string, ChatMessage[]>>(INITIAL_MESSAGES);
  const [loading, setLoading] = useState(false);
  const botReplyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedConversationId) ?? null,
    [conversations, selectedConversationId],
  );

  const messages = useMemo(
    () => (selectedConversationId ? messagesByConversation[selectedConversationId] ?? [] : []),
    [messagesByConversation, selectedConversationId],
  );

  const selectConversation = (id: string) => {
    setSelectedConversationId(id);
  };

  const sendMessage = (content: string) => {
    const trimmed = content.trim();
    if (!trimmed || !selectedConversationId) return;

    const userMessage: ChatMessage = {
      id: `m-${Date.now()}`,
      sender: 'user',
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    setMessagesByConversation((current) => {
      const currentMessages = current[selectedConversationId] ?? [];
      return {
        ...current,
        [selectedConversationId]: [...currentMessages, userMessage],
      };
    });

    setConversations((current) =>
      current.map((conversation) =>
        conversation.id === selectedConversationId
          ? {
              ...conversation,
              lastMessage: trimmed,
            }
          : conversation,
      ),
    );

    setLoading(true);

    if (botReplyTimerRef.current) {
      clearTimeout(botReplyTimerRef.current);
    }

    botReplyTimerRef.current = setTimeout(() => {
      const botMessage: ChatMessage = {
        id: `m-${Date.now()}-bot`,
        sender: 'bot',
        content: buildBotReply(trimmed),
        createdAt: new Date().toISOString(),
      };

      setMessagesByConversation((current) => {
        const currentMessages = current[selectedConversationId] ?? [];
        return {
          ...current,
          [selectedConversationId]: [...currentMessages, botMessage],
        };
      });

      setConversations((current) =>
        current.map((conversation) =>
          conversation.id === selectedConversationId
            ? {
                ...conversation,
                lastMessage: botMessage.content,
              }
            : conversation,
        ),
      );

      setLoading(false);
    }, 700);
  };

  useEffect(() => {
    return () => {
      if (botReplyTimerRef.current) {
        clearTimeout(botReplyTimerRef.current);
      }
    };
  }, []);

  return {
    conversations,
    selectedConversation,
    messages,
    loading,
    sendMessage,
    selectConversation,
  };
}
