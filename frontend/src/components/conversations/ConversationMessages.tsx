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
    <div className="h-full px-4 pb-6 pt-4 md:px-6">
      {loading ? (
        <div className="flex h-full flex-col items-center justify-center gap-2 text-slate-400">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-sky-500" />
          <p className="text-sm">Cargando mensajes...</p>
        </div>
      ) : messages.length === 0 ? (
        <div className="flex h-full flex-col items-center justify-center gap-3 text-slate-400">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-white text-slate-300 ring-1 ring-slate-200">
            <MessageSquare className="h-5 w-5" />
          </span>
          <p className="text-sm font-medium text-slate-500">No hay mensajes aun</p>
        </div>
      ) : (
        <>
          {messages.map((msg, idx) => {
            const prev = idx > 0 ? messages[idx - 1] : null;
            const showBoundary =
              Boolean(msg.isNewConversationBoundary) ||
              (prev ? prev.conversationId !== msg.conversationId : false);
            const grouped = prev?.direction === msg.direction;
            return (
              <div key={msg.id}>
                {showBoundary && (
                  <div className="my-5 flex items-center gap-3">
                    <div className="h-px flex-1 bg-slate-200" />
                    <div className="rounded-full border border-slate-200 bg-white px-3 py-1 shadow-sm">
                      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                        Nueva conversacion{msg.conversationType ? ` · ${msg.conversationType}` : ''}
                        {msg.conversationStartedAt
                          ? ` · ${new Date(msg.conversationStartedAt).toLocaleString('es-AR')}`
                          : ''}
                      </p>
                    </div>
                    <div className="h-px flex-1 bg-slate-200" />
                  </div>
                )}
                <ConversationMessage
                  message={msg}
                  grouped={grouped && !showBoundary}
                  onRetry={onRetry}
                />
              </div>
            );
          })}
        </>
      )}
      <div ref={bottomRef} className="h-2" />
    </div>
  );
}
