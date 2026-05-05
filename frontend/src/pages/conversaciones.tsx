import { useState } from 'react';
import { X } from 'lucide-react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import ConversationsSidebar from '@/components/conversations/ConversationsSidebar';
import ConversationView from '@/components/conversations/ConversationView';
import { useConversations } from '@/hooks/useConversations';
import { getChannelConfig } from '@/services/channelConfig';

export default function ConversationsPage() {
  const router = useRouter();
  const [showListOnMobile, setShowListOnMobile] = useState(true);
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
    togglingModes,
    configStatusByConversation,
  } = useConversations();

  const selectedStatus = selectedId ? configStatusByConversation[selectedId] : undefined;
  const isAiUnavailable = !!selectedStatus && !selectedStatus.is_valid;
  const aiUnavailableReason = isAiUnavailable
    ? selectedStatus?.missing_fields?.length
      ? `Completa la configuracion del bot para activar la IA (faltan: ${selectedStatus.missing_fields.join(', ')})`
      : 'Completa la configuracion del bot para activar la IA'
    : undefined;

  const hasSelectedConversation = !!selectedConversation;
  const showSidebarMobile = showListOnMobile || !hasSelectedConversation;
  const showChatMobile = !showListOnMobile && hasSelectedConversation;

  return (
    <AppLayout>
      <div className="flex h-full min-h-0 flex-1 flex-col overflow-hidden">
        {error && (
          <div className="flex flex-shrink-0 items-center justify-between border-b border-red-200 bg-red-50 px-4 py-2">
            <span className="text-sm text-red-700">{error}</span>
            <button
              onClick={dismissError}
              className="ml-4 text-red-400 transition-colors hover:text-red-600"
              aria-label="Cerrar error"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        <div className="chat-layout flex h-full min-h-0 flex-1 overflow-hidden">
          <div
            className={`${showSidebarMobile ? 'flex' : 'hidden'} h-full min-h-0 w-full md:flex md:w-auto`}
          >
            <ConversationsSidebar
              conversations={conversations}
              selectedId={selectedId}
              onSelect={(id) => {
                selectConversation(id);
                setShowListOnMobile(false);
              }}
              loading={loadingConversations}
            />
          </div>

          <div className={`${showChatMobile ? 'flex' : 'hidden'} h-full min-h-0 flex-1 md:flex`}>
            <ConversationView
              conversation={selectedConversation}
              messages={messages[selectedId] ?? []}
              onSend={handleSend}
              onRetry={retryMessage}
              loading={loadingMessages}
              onModeToggle={toggleMode}
              isToggling={togglingModes[selectedId]}
              aiUnavailable={isAiUnavailable}
              aiUnavailableReason={aiUnavailableReason}
              onOpenConfig={() => {
                const openConfig = async () => {
                  try {
                    const channelId = selectedConversation?.channelId;
                    if (channelId) {
                      await router.push(`/configuracion?id=${channelId}`);
                      return;
                    }

                    const configId = selectedConversation?.channelConfigId;
                    if (!configId) return;

                    const channelConfig = await getChannelConfig(configId);
                    if (channelConfig?.channel_id) {
                      await router.push(`/configuracion?id=${channelConfig.channel_id}`);
                    }
                  } catch {
                    // noop
                  }
                };

                void openConfig();
              }}
              onBackToList={() => setShowListOnMobile(true)}
            />
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
