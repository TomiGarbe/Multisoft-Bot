import { Phone } from 'lucide-react';
import { Conversation } from '@/types/chat';

interface Props {
  conversation: Conversation;
  onModeToggle?: (conversationId: string, mode: 'ai' | 'human') => void;
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

export default function ConversationHeader({ conversation, onModeToggle }: Props) {
  const initials = getInitials(conversation.contactName);
  const color = avatarColor(conversation.id);

  return (
    <div className="flex-shrink-0 flex items-center gap-3 px-5 py-3 border-b border-gray-200 bg-white shadow-sm">
      {/* Avatar */}
      <div
        className={`w-10 h-10 rounded-full ${color} flex items-center justify-center text-white font-semibold text-sm flex-shrink-0 select-none`}
      >
        {initials}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h2 className="font-semibold text-gray-900 text-sm">
            {conversation.contactName}
          </h2>
          <span
            className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full ${
              conversation.status === 'open'
                ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
                : 'bg-gray-100 text-gray-500 ring-1 ring-gray-200'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                conversation.status === 'open'
                  ? 'bg-emerald-500'
                  : 'bg-gray-400'
              }`}
            />
            {conversation.status === 'open' ? 'Abierta' : 'Cerrada'}
          </span>
        </div>

        {conversation.contactPhone && (
          <div className="flex items-center gap-1 mt-0.5">
            <Phone className="w-3 h-3 text-gray-400" />
            <span className="text-xs text-gray-400">
              {conversation.contactPhone}
            </span>
          </div>
        )}
      </div>

      {/* Mode badge — clickable when onModeToggle is provided */}
      <button
        onClick={
          onModeToggle
            ? () =>
                onModeToggle(
                  conversation.id,
                  conversation.mode === 'ai' ? 'human' : 'ai',
                )
            : undefined
        }
        disabled={!onModeToggle}
        title={onModeToggle ? 'Cambiar modo' : undefined}
        className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider transition-opacity ${
          conversation.mode === 'ai'
            ? 'bg-emerald-100 text-emerald-700'
            : 'bg-blue-100 text-blue-700'
        } ${onModeToggle ? 'cursor-pointer hover:opacity-75' : 'cursor-default'}`}
      >
        {conversation.mode === 'ai' ? 'AI' : 'Humano'}
      </button>
    </div>
  );
}
