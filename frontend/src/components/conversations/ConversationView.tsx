import { ChevronLeft, MessageSquare } from 'lucide-react';
import { Conversation, Message, SendPayload, UserTypeDefinition } from '@/types/chat';
import ConversationHeader from './ConversationHeader';
import ConversationMessages from './ConversationMessages';
import MessageComposer from './MessageComposer';
import { getChannelMeta, type ChannelMeta } from './channelMeta';

interface Props {
  conversation: Conversation | undefined;
  messages: Message[];
  onSend: (payload: SendPayload) => void;
  onRetry?: (messageId: string) => void;
  loading?: boolean;
  onModeToggle?: (conversationId: string, mode: 'ai' | 'human') => void;
  isToggling?: boolean;
  aiUnavailable?: boolean;
  aiUnavailableReason?: string;
  onOpenConfig?: () => void;
  onBackToList?: () => void;
  channelMeta?: ChannelMeta;
  userTypeOptions?: UserTypeDefinition[];
  userTypeMap?: Record<string, UserTypeDefinition>;
  onContactTypeChange?: (contactId: string, typeKey: string) => Promise<void>;
}

export default function ConversationView({
  conversation,
  messages,
  onSend,
  onRetry,
  loading = false,
  onModeToggle,
  isToggling,
  aiUnavailable,
  aiUnavailableReason,
  onOpenConfig,
  onBackToList,
  channelMeta,
  userTypeOptions = [],
  userTypeMap = {},
  onContactTypeChange,
}: Props) {
  if (!conversation) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 bg-slate-50 text-slate-400">
        <span className="flex h-16 w-16 items-center justify-center rounded-full bg-white text-slate-300 shadow-sm ring-1 ring-slate-200">
          <MessageSquare className="h-7 w-7" />
        </span>
        <p className="text-sm font-medium text-slate-500">
          Selecciona una conversacion para comenzar
        </p>
      </div>
    );
  }

  return (
    <div className="chat flex min-h-0 flex-1 flex-col overflow-hidden bg-slate-50">
      <div className="chat-header flex-shrink-0">
        <div className="border-b border-slate-200 bg-white px-3 py-2 md:hidden">
          <button
            type="button"
            onClick={onBackToList}
            className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            <ChevronLeft className="h-3.5 w-3.5" />
            Conversaciones
          </button>
        </div>
        <ConversationHeader
          conversation={conversation}
          channelMeta={channelMeta ?? getChannelMeta()}
          onModeToggle={onModeToggle}
          isToggling={isToggling}
          aiUnavailable={aiUnavailable}
          aiUnavailableReason={aiUnavailableReason}
          onOpenConfig={onOpenConfig}
          userTypeOptions={userTypeOptions}
          userTypeMap={userTypeMap}
          onContactTypeChange={onContactTypeChange}
        />
      </div>
      <div className="chat-messages scrollbar-thin min-h-0 flex-1 overflow-y-auto">
        <ConversationMessages messages={messages} loading={loading} onRetry={onRetry} />
      </div>
      <div className="chat-input flex-shrink-0 border-t border-slate-200 bg-white">
        <MessageComposer onSend={onSend} />
      </div>
    </div>
  );
}
