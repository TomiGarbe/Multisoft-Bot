import { useEffect, useRef } from 'react';
import { MessageSquare } from 'lucide-react';
import { Message } from '@/types/chat';
import ConversationMessage from './ConversationMessage';

interface Props {
  messages: Message[];
  loading?: boolean;
  onRetry?: (messageId: string) => void;
}

export default function ConversationMessages({ messages, loading = false, onRetry }: Props) {
  console.warn('[PIPELINE][FRONTEND_RENDER]', {
    messages: messages.length,
    loading,
  });
  const bottomRef = useRef<HTMLDivElement>(null);
  const previousCountRef = useRef(0);

  useEffect(() => {
    const previousCount = previousCountRef.current;
    const currentCount = messages.length;
    const behavior: ScrollBehavior = previousCount === 0 ? 'auto' : 'smooth';
    bottomRef.current?.scrollIntoView({ behavior });
    previousCountRef.current = currentCount;
  }, [messages]);

  return (
    <div className="h-full px-4 py-4">
      {loading ? (
        <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-400">
          <div className="w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
          <p className="text-sm">Cargando mensajes...</p>
        </div>
      ) : messages.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-full gap-2 text-gray-400">
          <MessageSquare className="w-8 h-8 opacity-30" />
          <p className="text-sm">No hay mensajes aun</p>
        </div>
      ) : (
        <>
          {messages.map((msg, idx) => {
            const prev = idx > 0 ? messages[idx - 1] : null;
            const grouped = prev?.direction === msg.direction;
            return (
              <ConversationMessage
                key={msg.id}
                message={msg}
                grouped={grouped}
                onRetry={onRetry}
              />
            );
          })}
        </>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
