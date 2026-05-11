import type { LucideIcon } from 'lucide-react';
import { Camera, Globe, MessageCircle, Send, Smartphone } from 'lucide-react';
import type { Channel } from '@/types/channel';

export type ConversationChannelKey = 'whatsapp' | 'instagram' | 'telegram' | 'webchat' | 'canal';

export interface ChannelMeta {
  key: ConversationChannelKey;
  label: string;
  Icon: LucideIcon;
  badgeClassName: string;
}

export function normalizeChannelKey(value?: string | null): ConversationChannelKey {
  const normalized = (value ?? '').trim().toLowerCase();
  if (!normalized) return 'canal';
  if (normalized.includes('whatsapp')) return 'whatsapp';
  if (normalized.includes('instagram')) return 'instagram';
  if (normalized.includes('telegram')) return 'telegram';
  if (normalized.includes('web')) return 'webchat';
  return 'canal';
}

export function getChannelMeta(channel?: Channel | null): ChannelMeta {
  const key = normalizeChannelKey(channel?.type);
  const provider = typeof channel?.config?.provider === 'string' ? channel.config.provider : '';
  const displayName = channel?.name?.trim() || channel?.type?.trim() || 'Sin canal';
  const label = provider ? `${displayName} (${provider})` : displayName;

  if (key === 'whatsapp') {
    return {
      key,
      label,
      Icon: MessageCircle,
      badgeClassName: 'bg-emerald-100 text-emerald-700 ring-emerald-200',
    };
  }

  if (key === 'instagram') {
    return {
      key,
      label,
      Icon: Camera,
      badgeClassName: 'bg-pink-100 text-pink-700 ring-pink-200',
    };
  }

  if (key === 'telegram') {
    return {
      key,
      label,
      Icon: Send,
      badgeClassName: 'bg-sky-100 text-sky-700 ring-sky-200',
    };
  }

  if (key === 'webchat') {
    return {
      key,
      label,
      Icon: Globe,
      badgeClassName: 'bg-slate-100 text-slate-700 ring-slate-200',
    };
  }

  return {
    key: 'canal',
    label,
    Icon: Smartphone,
    badgeClassName: 'bg-gray-100 text-gray-700 ring-gray-200',
  };
}
