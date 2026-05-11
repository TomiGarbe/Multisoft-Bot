import { ChevronLeft, MessageSquare } from 'lucide-react';
import { Conversation, Message, SendPayload } from '@/types/chat';
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
}: Props) {
  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 gap-3 text-gray-400">
        <MessageSquare className="w-12 h-12 opacity-20" />
        <p className="text-sm">
          Selecciona una conversacion para comenzar
        </p>
      </div>
    );
  }

  return (
    <div className="chat flex min-h-0 flex-1 flex-col bg-gray-50">
      <div className="chat-header flex-shrink-0">
        <div className="border-b border-gray-200 bg-white px-3 py-2 md:hidden">
          <button
            type="button"
            onClick={onBackToList}
            className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-xs font-medium text-gray-700"
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
        />
      </div>
      <div className="chat-messages flex-1 min-h-0 overflow-y-auto">
        <ConversationMessages messages={messages} loading={loading} onRetry={onRetry} />
      </div>
      <div className="chat-input flex-shrink-0">
        <MessageComposer onSend={onSend} />
      </div>
    </div>
  );
}
