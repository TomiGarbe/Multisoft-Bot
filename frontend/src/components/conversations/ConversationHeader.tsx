import { Bot, Check, ChevronDown, Phone, User } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
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
  const [typeMenuOpen, setTypeMenuOpen] = useState(false);
  const typeMenuRef = useRef<HTMLDivElement | null>(null);
  const userTypeLabel = useMemo(() => {
    const key = conversation.contactCurrentType ?? '';
    return userTypeMap[key]?.label ?? key ?? 'Sin tipo';
  }, [conversation.contactCurrentType, userTypeMap]);
  const userTypeColor = useMemo(() => {
    const key = conversation.contactCurrentType ?? '';
    return userTypeMap[key]?.color ?? '#94a3b8';
  }, [conversation.contactCurrentType, userTypeMap]);

  const typeOptions = useMemo(() => {
    return userTypeOptions.length > 0
      ? userTypeOptions
      : [{ key: '', label: 'Sin tipo', color: '#94a3b8' }];
  }, [userTypeOptions]);

  const currentTypeKey = conversation.contactCurrentType ?? '';
  const typeDisabled = !onContactTypeChange || updatingType;

  useEffect(() => {
    if (!typeMenuOpen) return;
    const handler = (event: MouseEvent) => {
      if (!typeMenuRef.current?.contains(event.target as Node)) {
        setTypeMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [typeMenuOpen]);

  const handleSelectType = async (nextKey: string) => {
    setTypeMenuOpen(false);
    if (!onContactTypeChange) return;
    if (nextKey === currentTypeKey) return;
    setUpdatingType(true);
    try {
      await onContactTypeChange(conversation.id, nextKey);
    } finally {
      setUpdatingType(false);
    }
  };

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
        <div className="relative w-48" ref={typeMenuRef}>
          <button
            type="button"
            id={`contact-type-${conversation.id}`}
            disabled={typeDisabled}
            onClick={() => setTypeMenuOpen((v) => !v)}
            aria-haspopup="listbox"
            aria-expanded={typeMenuOpen}
            className={`flex h-9 w-full items-center gap-2 rounded-xl border px-3 text-left text-sm font-semibold outline-none transition-all duration-150 disabled:cursor-not-allowed disabled:opacity-70 ${
              typeMenuOpen ? 'ring-2' : 'hover:brightness-95'
            }`}
            style={{
              backgroundColor: `${userTypeColor}1A`,
              borderColor: `${userTypeColor}66`,
              color: userTypeColor,
              boxShadow: typeMenuOpen ? `0 0 0 2px ${userTypeColor}33` : undefined,
            }}
          >
            <span
              aria-hidden
              className="h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-white"
              style={{ backgroundColor: userTypeColor, boxShadow: `0 0 0 1px ${userTypeColor}80` }}
            />
            <span className="flex-1 truncate">{userTypeLabel}</span>
            {updatingType ? (
              <span
                aria-hidden
                className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent opacity-70"
              />
            ) : (
              <ChevronDown
                className={`h-3.5 w-3.5 shrink-0 transition-transform duration-150 ${typeMenuOpen ? 'rotate-180' : ''}`}
              />
            )}
          </button>

          {typeMenuOpen ? (
            <div className="animate-popover absolute left-0 right-0 z-50 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg ring-1 ring-black/5">
              <ul role="listbox" className="scrollbar-thin max-h-64 overflow-y-auto py-1">
                {typeOptions.map((option) => {
                  const isSelected = option.key === currentTypeKey;
                  return (
                    <li key={option.key || '__placeholder__'}>
                      <button
                        type="button"
                        role="option"
                        aria-selected={isSelected}
                        onClick={() => void handleSelectType(option.key)}
                        className={`flex w-full items-center gap-2.5 px-3 py-2 text-left text-sm transition-colors ${
                          isSelected ? 'font-semibold' : 'hover:bg-slate-50'
                        }`}
                        style={{
                          backgroundColor: isSelected ? `${option.color}14` : undefined,
                          color: isSelected ? option.color : '#334155',
                        }}
                      >
                        <span
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-lg"
                          style={{
                            backgroundColor: `${option.color}22`,
                            border: `1px solid ${option.color}55`,
                          }}
                        >
                          <span
                            aria-hidden
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: option.color }}
                          />
                        </span>
                        <span className="min-w-0 flex-1 truncate">{option.label}</span>
                        {isSelected ? (
                          <Check
                            className="h-4 w-4 shrink-0"
                            style={{ color: option.color }}
                            strokeWidth={3}
                          />
                        ) : null}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}
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
