'use client';

import AppLayout from '@/components/layout/AppLayout';
import ChannelForm from '@/components/channels/ChannelForm';
import Button from '@/components/ui/Button';
import { ToastViewport, useToast } from '@/components/ui/toast';
import ChannelsTable from '@/components/channels/ChannelsTable';
import { useChannelsPage } from '@/hooks/channels/useChannelsPage';

export default function ChannelsPage() {
  const toast = useToast();

  const {
    hasToken,
    channels,
    isLoading,
    error,
    isDeletingId,
    isFormOpen,
    selectedChannel,
    openCreate,
    openEdit,
    handleDelete,
    setIsFormOpen,
    loadChannels,
  } = useChannelsPage(toast);

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />

      <div className="space-y-6 p-6 md:p-8">
        <section className="flex flex-col items-start justify-between gap-4 rounded-2xl border bg-white p-6 shadow-sm md:flex-row md:items-center">
          <div>
            <h1 className="text-3xl font-bold">Channels</h1>
            <p className="mt-2 text-sm text-slate-600">
              Manage communication channels across multiple platforms.
            </p>
          </div>

          <Button onClick={openCreate}>+ Create Channel</Button>
        </section>

        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="text-center text-sm text-slate-500">
            Loading channels...
          </div>
        ) : (
          <ChannelsTable
            channels={channels}
            isDeletingId={isDeletingId}
            onEdit={openEdit}
            onDelete={handleDelete}
          />
        )}
      </div>

      <ChannelForm
        isOpen={isFormOpen}
        channel={selectedChannel}
        onClose={() => setIsFormOpen(false)}
        onSaved={(message) => {
          toast.success(message);
          void loadChannels();
        }}
      />
    </AppLayout>
  );
}
