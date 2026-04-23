import api from '@/services/api';
import type { Channel, ChannelCreate, ChannelUpdate } from '@/types/channel';

export async function getChannels(): Promise<Channel[]> {
  const { data } = await api.get<Channel[]>('/channels');
  return data;
}

export async function createChannel(payload: ChannelCreate): Promise<Channel> {
  const { data } = await api.post<Channel>('/channels', payload);
  return data;
}

export async function updateChannel(channelId: string, payload: ChannelUpdate): Promise<Channel> {
  const { data } = await api.put<Channel>(`/channels/${channelId}`, payload);
  return data;
}

export async function deleteChannel(channelId: string): Promise<void> {
  await api.delete(`/channels/${channelId}`);
}
