import { Bot, Phone, User } from 'lucide-react';
import { useMemo, useState } from 'react';
import Select from '@/components/ui/Select';
import { Conversation, UserTypeDefinition } from '@/types/chat';
import type { ChannelMeta } from './channelMeta';

interface Props {
  conversation: Conversation;
  onModeToggle?: (conversationId: string, mode: 'ai' | 'human') => void;
  isToggling?: boolean;
  aiUnavailable?: boolean;
  aiUnavailableReason?: string;
  onOpenConfig?: () => void;
  channelMeta: ChannelMeta;
  userTypeOptions?: UserTypeDefinition[];
  userTypeMap?: Record<string, UserTypeDefinition>;
  onContactTypeChange?: (contactId: string, typeKey: string) => Promise<void>;
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

export default function ConversationHeader({
  conversation,
  onModeToggle,
  isToggling,
  aiUnavailable,
  aiUnavailableReason,
  onOpenConfig,
  channelMeta,
  userTypeOptions = [],
  userTypeMap = {},
  onContactTypeChange,
}: Props) {
  const initials = getInitials(conversation.contactName);
  const color = avatarColor(conversation.id);

  const canClickToggle =
    !!onModeToggle && !isToggling && !(aiUnavailable && conversation.mode === 'human');
  const ChannelIcon = channelMeta.Icon;
  const [updatingType, setUpdatingType] = useState(false);
  const userTypeLabel = useMemo(() => {
    const key = conversation.contactCurrentType ?? '';
    return userTypeMap[key]?.label ?? key ?? 'Sin tipo';
  }, [conversation.contactCurrentType, userTypeMap]);

  const typeSelectOptions = useMemo(() => {
    const base =
      userTypeOptions.length > 0
        ? userTypeOptions
        : [{ key: '', label: 'Sin tipo', color: '#94a3b8' }];
    return base.map((option) => ({
      value: option.key,
      label: option.label,
      icon: (
        <span
          aria-hidden
          className="h-3 w-3 rounded-full ring-2 ring-white shadow-sm"
          style={{ backgroundColor: option.color }}
        />
      ),
    }));
  }, [userTypeOptions]);

  return (
    <div className="flex min-h-[88px] flex-shrink-0 flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div
        className={`flex h-10 w-10 flex-shrink-0 select-none items-center justify-center rounded-full text-sm font-semibold text-white ${color}`}
      >
        {initials}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-sm font-semibold text-slate-900">{conversation.contactName}</h2>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ${channelMeta.badgeClassName}`}
          >
            <ChannelIcon className="h-3 w-3" />
            {channelMeta.label}
          </span>
          <span
            className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ring-1 ring-inset ${
              conversation.status === 'open'
                ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
                : 'bg-slate-100 text-slate-500 ring-slate-200'
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                conversation.status === 'open' ? 'bg-emerald-500' : 'bg-slate-400'
              }`}
            />
            {conversation.status === 'open' ? 'Abierta' : 'Cerrada'}
          </span>
        </div>

        {conversation.contactPhone && (
          <div className="mt-0.5 flex items-center gap-1 text-xs text-slate-400">
            <Phone className="h-3 w-3" />
            <span>{conversation.contactPhone}</span>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="w-44">
          <Select
            id={`contact-type-${conversation.id}`}
            size="sm"
            value={conversation.contactCurrentType ?? ''}
            options={typeSelectOptions}
            disabled={!onContactTypeChange || updatingType}
            onChange={async (event) => {
              if (!onContactTypeChange) return;
              setUpdatingType(true);
              try {
                await onContactTypeChange(conversation.id, event.target.value);
              } finally {
                setUpdatingType(false);
              }
            }}
            placeholder={userTypeLabel}
          />
        </div>

        <button
          onClick={
            canClickToggle
              ? () => onModeToggle?.(conversation.id, conversation.mode === 'ai' ? 'human' : 'ai')
              : undefined
          }
          disabled={!canClickToggle}
          title={onModeToggle ? 'Cambiar modo' : undefined}
          aria-busy={isToggling ? true : undefined}
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-bold uppercase tracking-wide transition-all duration-150 ring-1 ring-inset ${
            aiUnavailable
              ? 'bg-rose-50 text-rose-700 ring-rose-200'
              : conversation.mode === 'ai'
                ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
                : 'bg-sky-50 text-sky-700 ring-sky-200'
          } ${
            canClickToggle
              ? 'cursor-pointer hover:opacity-80 active:scale-95'
              : isToggling
                ? 'cursor-wait'
                : 'cursor-not-allowed opacity-90'
          }`}
        >
          {aiUnavailable ? (
            <span className="h-1.5 w-1.5 rounded-full bg-rose-600" />
          ) : conversation.mode === 'ai' ? (
            <Bot className="h-3 w-3" />
          ) : (
            <User className="h-3 w-3" />
          )}
          <span className="whitespace-nowrap">
            {aiUnavailable ? 'IA no disponible' : conversation.mode === 'ai' ? 'IA activa' : 'Humano'}
          </span>
        </button>
      </div>

      {aiUnavailable && (
        <button
          type="button"
          onClick={onOpenConfig}
          className="basis-full text-xs text-rose-700 underline underline-offset-2 transition-colors hover:text-rose-800"
          title="Ir a configuracion"
        >
          {aiUnavailableReason ?? 'Completa la configuracion del bot para activar la IA'}
        </button>
      )}
    </div>
  );
}
