import { Conversation } from '@/types/chat';
import ChannelSelector from '@/components/shared/ChannelSelector';
import ConversationsFilters from './ConversationsFilters';
import type { ChannelMeta } from './channelMeta';

interface Props {
  conversations: Conversation[];
  totalConversations: number;
  openConversations: number;
  selectedId: string;
  onSelect: (id: string) => void;
  search: string;
  onSearchChange: (value: string) => void;
  selectedChannel: string;
  onChannelChange: (value: string) => void;
  selectedStatus: 'all' | 'open' | 'closed';
  onStatusChange: (value: 'all' | 'open' | 'closed') => void;
  channelOptions: Array<{ value: string; label: string }>;
  onClearFilters: () => void;
  getChannelMeta: (conversation: Conversation) => ChannelMeta;
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
    .map((word) => word[0])
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
  if (diffMins < 1440) {
    return date.toLocaleTimeString('es-AR', {
      hour: '2-digit',
      minute: '2-digit',
    });
  }
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
  totalConversations,
  openConversations,
  selectedId,
  onSelect,
  search,
  onSearchChange,
  selectedChannel,
  onChannelChange,
  selectedStatus,
  onStatusChange,
  channelOptions,
  onClearFilters,
  getChannelMeta,
  loading = false,
}: Props) {
  return (
    <div className="conversations-sidebar flex h-full min-h-0 w-full flex-shrink-0 flex-col overflow-hidden border-r border-gray-200 bg-white md:w-80">
      <div className="flex-shrink-0 border-b border-gray-100 px-5 py-4">
        <div className="flex items-center justify-between gap-2">
          <div>
            <h1 className="text-base font-semibold text-gray-900">Conversaciones</h1>
            <p className="mt-0.5 text-xs text-gray-400">
              {loading ? 'Cargando...' : `${openConversations} abiertas de ${totalConversations}`}
            </p>
          </div>
          <div className="w-40">
            <ChannelSelector
              label={null}
              value={selectedChannel}
              onChange={onChannelChange}
              options={[{ value: 'all', label: 'Todos' }, ...channelOptions]}
            />
          </div>
        </div>
      </div>

      <div className="flex-shrink-0 bg-white">
        <ConversationsFilters
          search={search}
          onSearchChange={onSearchChange}
          selectedChannel={selectedChannel}
          onChannelChange={onChannelChange}
          selectedStatus={selectedStatus}
          onStatusChange={onStatusChange}
          channelOptions={channelOptions}
          onClearFilters={onClearFilters}
          showChannelSelector={false}
        />
      </div>

      {loading ? (
        <SidebarSkeleton />
      ) : (
        <div className="conversation-list min-h-0 flex-1 overflow-y-auto">
          {conversations.map((conv) => {
            const isSelected = conv.id === selectedId;
            const initials = getInitials(conv.contactName);
            const color = avatarColor(conv.id);
            const channel = getChannelMeta(conv);
            const ChannelIcon = channel.Icon;

            return (
              <button
                key={conv.id}
                onClick={() => onSelect(conv.id)}
                className={`w-full flex items-start gap-3 px-4 py-3 text-left transition-colors border-l-2 ${
                  isSelected
                    ? 'bg-blue-50 border-l-blue-500'
                    : 'border-l-transparent hover:bg-gray-50'
                }`}
              >
                <div
                  className={`relative flex-shrink-0 w-11 h-11 rounded-full ${color} flex items-center justify-center text-white font-semibold text-sm select-none`}
                >
                  {initials}
                  {conv.status === 'open' && (
                    <span className="absolute bottom-0 right-0 w-3 h-3 bg-emerald-400 border-2 border-white rounded-full" />
                  )}
                </div>

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
                        <span className="text-[11px] text-gray-400">{formatTime(conv.lastMessageAt)}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between mt-0.5 gap-2">
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

                  <div className="mt-1">
                    <span
                      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ${channel.badgeClassName}`}
                    >
                      <ChannelIcon className="h-3 w-3" />
                      {channel.label}
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
          {!conversations.length && (
            <div className="px-4 py-8 text-center text-sm text-gray-500">
              No se encontraron resultados para los filtros seleccionados.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
