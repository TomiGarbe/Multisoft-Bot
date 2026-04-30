import type { Conversation } from '@/types/chat';

interface ConversationListProps {
  conversations: Conversation[];
  selected: Conversation | null;
  onSelect: (id: string) => void;
}

export default function ConversationList({ conversations, selected, onSelect }: ConversationListProps) {
  return (
    <aside className="w-full shrink-0 border border-slate-200 bg-white md:w-80 lg:w-96 md:border-r md:border-y-0 md:border-l-0">
      <div className="border-b border-slate-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-slate-900">Conversaciones</h3>
      </div>

      <div className="max-h-64 overflow-y-auto md:max-h-none md:h-[calc(100vh-11.5rem)]">
        {conversations.map((conversation) => {
          const isActive = selected?.id === conversation.id;

          return (
            <button
              key={conversation.id}
              type="button"
              onClick={() => onSelect(conversation.id)}
              className={`w-full border-b border-slate-100 px-4 py-3 text-left transition-colors ${
                isActive ? 'bg-sky-50' : 'hover:bg-slate-50'
              }`}
            >
              <p className="truncate text-sm font-medium text-slate-900">{conversation.contactName}</p>
              <p className="truncate text-xs text-slate-500">{conversation.lastMessage}</p>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
