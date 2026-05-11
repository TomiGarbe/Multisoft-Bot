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
    allConversations,
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
    search,
    selectedChannel,
    selectedStatus,
    channelOptions,
    stats,
    setSearch,
    setSelectedChannel,
    setSelectedStatus,
    clearFilters,
    resolveConversationChannel,
  } = useConversations();

  const selectedConversationStatus = selectedId ? configStatusByConversation[selectedId] : undefined;
  const isAiUnavailable = !!selectedConversationStatus && !selectedConversationStatus.is_valid;
  const aiUnavailableReason = isAiUnavailable
    ? selectedConversationStatus?.missing_fields?.length
      ? `Completa la configuracion del bot para activar la IA (faltan: ${selectedConversationStatus.missing_fields.join(', ')})`
      : 'Completa la configuracion del bot para activar la IA'
    : undefined;

  const hasSelectedConversation = !!selectedConversation;
  const hasAnyConversation = allConversations.length > 0;
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
              totalConversations={stats.total}
              openConversations={stats.open}
              selectedId={selectedId}
              onSelect={(id) => {
                selectConversation(id);
                setShowListOnMobile(false);
              }}
              search={search}
              onSearchChange={setSearch}
              selectedChannel={selectedChannel}
              onChannelChange={setSelectedChannel}
              selectedStatus={selectedStatus}
              onStatusChange={setSelectedStatus}
              channelOptions={channelOptions}
              onClearFilters={clearFilters}
              getChannelMeta={resolveConversationChannel}
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
              channelMeta={selectedConversation ? resolveConversationChannel(selectedConversation) : undefined}
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

        {!loadingConversations && !hasAnyConversation && (
          <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600">
            No hay conversaciones para este tenant.
          </div>
        )}

        {!loadingConversations && hasAnyConversation && conversations.length === 0 && (
          <div className="border-t border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600">
            No hay conversaciones para este canal o filtros. Ajusta los filtros para ver resultados.
          </div>
        )}
      </div>
    </AppLayout>
  );
}
