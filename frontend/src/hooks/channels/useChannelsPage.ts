import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/services/auth';
import { getApiErrorMessage } from '@/services/api';
import { getChannels, deleteChannel } from '@/services/channels';
import type { Channel } from '@/types/channel';

export function useChannelsPage(toast: any) {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const [channels, setChannels] = useState<Channel[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [selectedChannel, setSelectedChannel] = useState<Channel | null>(null);

  useEffect(() => {
    if (!hasToken) {
      router.replace('/login');
    }
  }, [hasToken, router]);

  const loadChannels = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await getChannels();
      setChannels(result);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load channels.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasToken) void loadChannels();
  }, [hasToken, loadChannels]);

  const openCreate = () => {
    setSelectedChannel(null);
    setIsFormOpen(true);
  };

  const openEdit = (channel: Channel) => {
    setSelectedChannel(channel);
    setIsFormOpen(true);
  };

  const handleDelete = async (channel: Channel) => {
    const confirmed = window.confirm(
      `Delete channel "${channel.name}"? This action cannot be undone.`,
    );
    if (!confirmed) return;

    try {
      setIsDeletingId(channel.id);
      await deleteChannel(channel.id);
      toast.success('Channel deleted successfully.');
      await loadChannels();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'Unable to delete channel.'));
    } finally {
      setIsDeletingId(null);
    }
  };

  return {
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
  };
}
