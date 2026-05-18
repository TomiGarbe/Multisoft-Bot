import { Bot, MessagesSquare, Search, User } from 'lucide-react';
import { Conversation } from '@/types/chat';
import ChannelSelector from '@/components/shared/ChannelSelector';
import Input from '@/components/ui/Input';
import ConversationsFilters from './ConversationsFilters';
import type { ChannelMeta } from './channelMeta';
import type { UserTypeDefinition } from '@/types/chat';

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
  selectedMode: 'all' | 'ai' | 'human';
  onModeChange: (value: 'all' | 'ai' | 'human') => void;
  selectedUserTypes: string[];
  onUserTypesChange: (value: string[]) => void;
  channelOptions: Array<{ value: string; label: string }>;
  userTypeOptions: UserTypeDefinition[];
  userTypeMap: Record<string, UserTypeDefinition>;
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
        <div
          key={i}
          className="flex items-center gap-3 border-l-2 border-l-transparent px-4 py-3"
        >
          <div className="h-11 w-11 flex-shrink-0 animate-pulse rounded-full bg-slate-200" />
          <div className="min-w-0 flex-1 space-y-2">
            <div className="h-3 w-3/4 animate-pulse rounded bg-slate-200" />
            <div className="h-2.5 w-1/2 animate-pulse rounded bg-slate-100" />
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
  selectedMode,
  onModeChange,
  selectedUserTypes,
  onUserTypesChange,
  channelOptions,
  userTypeOptions,
  userTypeMap,
  onClearFilters,
  getChannelMeta,
  loading = false,
}: Props) {
  return (
    <div className="conversations-sidebar scrollbar-thin flex h-full min-h-0 w-full flex-shrink-0 flex-col overflow-hidden border-r border-slate-200 bg-white md:w-80">
      <div className="flex h-[88px] flex-shrink-0 items-center border-b border-slate-100 px-3">
        <div className="w-full">
          <ChannelSelector
            label={null}
            value={selectedChannel}
            onChange={onChannelChange}
            options={[{ value: 'all', label: 'Todos' }, ...channelOptions]}
          />
        </div>
      </div>

      <div className="flex-shrink-0 bg-white">
        <div className="flex items-center justify-between px-3 pt-2">
          <span className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400">
            <MessagesSquare className="h-3 w-3" />
            {loading ? 'Cargando...' : `${openConversations} abiertas de ${totalConversations}`}
          </span>
        </div>
        <div className="px-3 pt-2">
          <Input
            id="conversations-search"
            value={search}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar nombre o contacto"
            leadingIcon={<Search />}
          />
        </div>
        <ConversationsFilters
          search={search}
          onSearchChange={onSearchChange}
          selectedMode={selectedMode}
          onModeChange={onModeChange}
          selectedUserTypes={selectedUserTypes}
          onUserTypesChange={onUserTypesChange}
          userTypeOptions={userTypeOptions}
          userTypeMap={userTypeMap}
          onClearFilters={onClearFilters}
        />
      </div>

      {loading ? (
        <SidebarSkeleton />
      ) : (
        <div className="conversation-list scrollbar-thin min-h-0 flex-1 overflow-y-auto">
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
                className={`flex w-full items-start gap-3 border-l-2 px-3 py-2.5 text-left transition-colors duration-150 ${
                  isSelected
                    ? 'border-l-sky-500 bg-sky-50'
                    : 'border-l-transparent hover:bg-slate-50'
                }`}
              >
                <div
                  className={`relative flex h-11 w-11 flex-shrink-0 select-none items-center justify-center rounded-full text-sm font-semibold text-white ${color}`}
                >
                  {initials}
                  {conv.status === 'open' && (
                    <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-white bg-emerald-400" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className={`truncate text-sm font-medium ${
                        isSelected ? 'text-sky-900' : 'text-slate-900'
                      }`}
                    >
                      {conv.contactName}
                    </span>

                    <div className="flex flex-shrink-0 items-center gap-1.5">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                          conv.mode === 'ai'
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-emerald-100 text-emerald-700'
                        }`}
                      >
                        {conv.mode === 'ai' ? (
                          <Bot className="h-3 w-3" />
                        ) : (
                          <User className="h-3 w-3" />
                        )}
                        {conv.mode === 'ai' ? 'AI' : 'Humano'}
                      </span>
                      {conv.lastMessageAt && (
                        <span className="text-[11px] text-slate-400">
                          {formatTime(conv.lastMessageAt)}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-0.5 flex items-center justify-between gap-2">
                    <p
                      className={`truncate text-xs ${
                        isSelected ? 'text-sky-700' : 'text-slate-500'
                      }`}
                    >
                      {conv.lastMessage ?? 'Sin mensajes'}
                    </p>
                    {(conv.unreadCount ?? 0) > 0 && (
                      <span className="ml-2 flex h-[18px] min-w-[18px] flex-shrink-0 items-center justify-center rounded-full bg-sky-600 px-1 text-[10px] font-bold text-white shadow-sm">
                        {conv.unreadCount}
                      </span>
                    )}
                  </div>

                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    {conv.contactCurrentType && userTypeMap[conv.contactCurrentType] && (
                      <span
                        className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ring-inset"
                        style={{
                          backgroundColor: `${userTypeMap[conv.contactCurrentType].color}20`,
                          color: userTypeMap[conv.contactCurrentType].color,
                          borderColor: `${userTypeMap[conv.contactCurrentType].color}55`,
                        }}
                      >
                        {userTypeMap[conv.contactCurrentType].label}
                      </span>
                    )}
                    {conv.contactCurrentType && !userTypeMap[conv.contactCurrentType] && (
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700 ring-1 ring-inset ring-slate-200">
                        {conv.contactCurrentType}
                      </span>
                    )}
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
            <div className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center">
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-50 text-slate-300 ring-1 ring-slate-200">
                <Search className="h-4 w-4" />
              </span>
              <p className="text-sm font-medium text-slate-600">Sin resultados</p>
              <p className="text-xs text-slate-500">
                Ajusta los filtros para ver mas conversaciones.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
