import { FormEvent, useEffect, useRef, useState } from 'react';
import Button from '@/components/ui/Button';
import type { ChatMessage } from '@/hooks/useConversations';

interface ChatWindowProps {
  messages: ChatMessage[];
  loading: boolean;
  onSend: (message: string) => void;
}

export default function ChatWindow({ messages, loading, onSend }: ChatWindowProps) {
  const [inputValue, setInputValue] = useState('');
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSend(inputValue);
    setInputValue('');
  };

  return (
    <section className="flex min-h-[450px] flex-1 flex-col border border-slate-200 bg-white md:min-h-0">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((message) => {
          const isUser = message.sender === 'user';

          return (
            <div key={message.id} className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm ${
                  isUser ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-800'
                }`}
              >
                {message.content}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-slate-100 px-3 py-2 text-sm text-slate-500">Escribiendo...</div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-slate-200 p-3">
        <input
          value={inputValue}
          onChange={(event) => setInputValue(event.target.value)}
          placeholder="Escribe un mensaje..."
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
        />
        <Button type="submit" disabled={!inputValue.trim() || loading}>
          Enviar
        </Button>
      </form>
    </section>
  );
}
