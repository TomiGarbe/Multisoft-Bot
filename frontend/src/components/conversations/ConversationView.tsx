import { MessageSquare } from 'lucide-react';
import { Conversation, Message, SendPayload } from '@/types/chat';
import ConversationHeader from './ConversationHeader';
import ConversationMessages from './ConversationMessages';
import MessageComposer from './MessageComposer';

interface Props {
  conversation: Conversation | undefined;
  messages: Message[];
  onSend: (payload: SendPayload) => void;
  onRetry?: (messageId: string) => void;
  loading?: boolean;
  onModeToggle?: (conversationId: string, mode: 'ai' | 'human') => void;
}

export default function ConversationView({
  conversation,
  messages,
  onSend,
  onRetry,
  loading = false,
  onModeToggle,
}: Props) {
  if (!conversation) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-gray-50 gap-3 text-gray-400">
        <MessageSquare className="w-12 h-12 opacity-20" />
        <p className="text-sm">
          Seleccioná una conversación para comenzar
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-gray-50">
      <ConversationHeader conversation={conversation} onModeToggle={onModeToggle} />
      <ConversationMessages messages={messages} loading={loading} onRetry={onRetry} />
      <MessageComposer onSend={onSend} />
    </div>
  );
}
