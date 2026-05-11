export type ChannelProviderId = 'multisoft' | 'web';

export interface ProviderOption {
  value: ChannelProviderId;
  label: string;
}

export const CHANNEL_PROVIDER_OPTIONS: ProviderOption[] = [
  { value: 'multisoft', label: 'Multisoft' },
  { value: 'web', label: 'Webchat' },
];

export const CHANNEL_PROVIDER_LABELS: Record<ChannelProviderId, string> = {
  multisoft: 'Multisoft',
  web: 'Webchat',
};
