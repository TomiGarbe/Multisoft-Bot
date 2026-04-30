import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import { Conversation } from '@/types/chat';

interface Props {
  conversations: Conversation[];
  selectedId: string;
  onSelect: (id: string) => void;
  loading?: boolean;
}

const AVATAR_COLORS = [
  'bg-indigo-500',
  'bg-violet-500',
  'bg-pink-500',
  'bg-rose-500',
  'bg-orange-500',
  'bg-emerald-500',
  'bg-teal-500',
  'bg-cyan-500',
];

function getInitials(name: string): string {
  return name
    .split(' ')
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
}

function avatarColor(id: string): string {
  const index =
    id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0) %
    AVATAR_COLORS.length;
  return AVATAR_COLORS[index];
}

function formatTime(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffMins = Math.floor((now.getTime() - date.getTime()) / 60_000);
  if (diffMins < 1) return 'ahora';
  if (diffMins < 60) return `${diffMins}m`;
  if (diffMins < 1440)
    return date.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  if (diffMins < 2880) return 'Ayer';
  return date.toLocaleDateString('es-AR', {
    day: '2-digit',
    month: '2-digit',
  });
}

function SidebarSkeleton() {
  return (
    <div className="flex-1 overflow-y-auto">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3 border-l-2 border-l-transparent">
          <div className="flex-shrink-0 w-11 h-11 rounded-full bg-gray-200 animate-pulse" />
          <div className="flex-1 min-w-0 space-y-2">
            <div className="h-3 bg-gray-200 rounded animate-pulse w-3/4" />
            <div className="h-2.5 bg-gray-100 rounded animate-pulse w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ConversationsSidebar({
  conversations,
  selectedId,
  onSelect,
  loading = false,
}: Props) {
  const [search, setSearch] = useState('');
  const query = search.trim().toLowerCase();
  const openCount = conversations.filter((c) => c.status === 'open').length;
  const filteredConversations = useMemo(() => {
    if (!query) return conversations;
    return conversations.filter((conv) => {
      const name = conv.contactName.toLowerCase();
      const phone = (conv.contactPhone ?? '').toLowerCase();
      return name.includes(query) || phone.includes(query);
    });
  }, [conversations, query]);

  return (
    <div className="sidebar flex h-full w-full flex-shrink-0 flex-col border-r border-gray-200 bg-white md:w-80">
      {/* Header */}
      <div className="flex-shrink-0 border-b border-gray-100 px-5 py-4">
        <h1 className="text-base font-semibold text-gray-900">
          Conversaciones
        </h1>
        <p className="text-xs text-gray-400 mt-0.5">
          {loading
            ? 'Cargando...'
            : `${openCount} abiertas de ${conversations.length}`}
        </p>
      </div>

      <div className="search-bar flex-shrink-0 border-b border-gray-100 p-3">
        <label className="relative block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por nombre o teléfono"
            className="w-full rounded-lg border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm text-gray-900 outline-none transition-colors focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          />
        </label>
      </div>

      {/* List */}
      {loading ? (
        <SidebarSkeleton />
      ) : (
      <div className="conversation-list flex-1 overflow-y-auto">
        {filteredConversations.map((conv) => {
          const isSelected = conv.id === selectedId;
          const initials = getInitials(conv.contactName);
          const color = avatarColor(conv.id);

          return (
            <button
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors border-l-2 ${
                isSelected
                  ? 'bg-blue-50 border-l-blue-500'
                  : 'border-l-transparent hover:bg-gray-50'
              }`}
            >
              {/* Avatar */}
              <div
                className={`relative flex-shrink-0 w-11 h-11 rounded-full ${color} flex items-center justify-center text-white font-semibold text-sm select-none`}
              >
                {initials}
                {conv.status === 'open' && (
                  <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-white rounded-full" />
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <span
                    className={`font-medium text-sm truncate ${
                      isSelected ? 'text-blue-900' : 'text-gray-900'
                    }`}
                  >
                    {conv.contactName}
                  </span>

                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide ${
                        conv.mode === 'ai'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {conv.mode === 'ai' ? 'AI' : 'HUM'}
                    </span>
                    {conv.lastMessageAt && (
                      <span className="text-[11px] text-gray-400">
                        {formatTime(conv.lastMessageAt)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between mt-0.5">
                  <p
                    className={`text-xs truncate ${
                      isSelected ? 'text-blue-700' : 'text-gray-500'
                    }`}
                  >
                    {conv.lastMessage ?? 'Sin mensajes'}
                  </p>
                  {(conv.unreadCount ?? 0) > 0 && (
                    <span className="flex-shrink-0 ml-2 min-w-[18px] h-[18px] bg-blue-500 rounded-full text-[10px] text-white font-bold flex items-center justify-center px-1">
                      {conv.unreadCount}
                    </span>
                  )}
                </div>
              </div>
            </button>
          );
        })}
        {!filteredConversations.length && (
          <div className="px-4 py-8 text-center text-sm text-gray-500">
            No hay conversaciones que coincidan con la búsqueda.
          </div>
        )}
      </div>
      )}
    </div>
  );
}
