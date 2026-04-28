import AppLayout from '@/components/layout/AppLayout';
import ConversationList from '@/components/conversations/ConversationList';
import ChatWindow from '@/components/conversations/ChatWindow';
import { useConversations } from '@/hooks/useConversations';

export default function ConversacionesPage() {
  const { conversations, selectedConversation, messages, loading, selectConversation, sendMessage } =
    useConversations();

  return (
    <AppLayout>
      <div className="flex h-full flex-col gap-4 p-4 md:p-6 lg:flex-row">
        <ConversationList
          conversations={conversations}
          onSelect={selectConversation}
          selected={selectedConversation}
        />
        <ChatWindow messages={messages} loading={loading} onSend={sendMessage} />
      </div>
    </AppLayout>
  );
}
