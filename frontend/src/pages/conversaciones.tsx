import { X } from 'lucide-react';
import AppLayout from '@/components/layout/AppLayout';
import ConversationsSidebar from '@/components/conversations/ConversationsSidebar';
import ConversationView from '@/components/conversations/ConversationView';
import { useConversations } from '@/hooks/useConversations';

export default function ConversationsPage() {
  const {
    conversations,
    selectedId,
    selectedConversation,
    messages,
    loadingConversations,
    loadingMessages,
    error,
    selectConversation,
    handleSend,
    retryMessage,
    toggleMode,
    dismissError,
  } = useConversations();

  return (
    <AppLayout>
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {error && (
          <div className="flex-shrink-0 flex items-center justify-between bg-red-50 border-b border-red-200 px-4 py-2">
            <span className="text-sm text-red-700">{error}</span>
            <button
              onClick={dismissError}
              className="ml-4 text-red-400 hover:text-red-600 transition-colors"
              aria-label="Cerrar error"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <div className="flex-1 flex min-h-0 overflow-hidden">
          <ConversationsSidebar
            conversations={conversations}
            selectedId={selectedId}
            onSelect={selectConversation}
            loading={loadingConversations}
          />
          <ConversationView
            conversation={selectedConversation}
            messages={messages[selectedId] ?? []}
            onSend={handleSend}
            onRetry={retryMessage}
            loading={loadingMessages}
            onModeToggle={toggleMode}
          />
        </div>
      </div>
    </AppLayout>
  );
}
