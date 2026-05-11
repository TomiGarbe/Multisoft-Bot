import type { ChannelProviderId, ProviderOption } from '@/constants/channelProviders';

export type ChannelType = 'whatsapp' | 'web';

export interface DynamicFieldDefinition {
  key: 'phone';
  label: string;
  placeholder: string;
  required: boolean;
}

export interface ChannelTypeDefinition {
  value: ChannelType;
  label: string;
  providers: ProviderOption[];
  fieldsByProvider?: Partial<Record<ChannelProviderId, DynamicFieldDefinition[]>>;
}

export const CHANNEL_TYPE_DEFINITIONS: ChannelTypeDefinition[] = [
  {
    value: 'whatsapp',
    label: 'WhatsApp',
    providers: [{ value: 'multisoft', label: 'Multisoft' }],
    fieldsByProvider: {
      multisoft: [
        {
          key: 'phone',
          label: 'Telefono',
          placeholder: '+54 9 351 XXX XXXX',
          required: true,
        },
      ],
    },
  },
  {
    value: 'web',
    label: 'Webchat',
    providers: [{ value: 'web', label: 'Webchat' }],
  },
];

export const CHANNEL_TYPE_LABELS: Record<ChannelType, string> = {
  whatsapp: 'WhatsApp',
  web: 'Webchat',
};

