import type { ChannelType, DynamicFieldDefinition } from '@/components/channels/channelFormConfig';
import type { ChannelProviderId, ProviderOption } from '@/constants/channelProviders';
import { CHANNEL_TYPE_DEFINITIONS } from '@/components/channels/channelFormConfig';

export function getTypeDefinition(type: string) {
  return CHANNEL_TYPE_DEFINITIONS.find((item) => item.value === type) ?? CHANNEL_TYPE_DEFINITIONS[0];
}

export function getProviderOptions(type: string): ProviderOption[] {
  return getTypeDefinition(type).providers;
}

export function getDynamicFields(type: string, provider: string): DynamicFieldDefinition[] {
  const typeConfig = getTypeDefinition(type);
  const fieldsByProvider = typeConfig.fieldsByProvider;

  if (!fieldsByProvider) return [];

  return fieldsByProvider[provider as ChannelProviderId] ?? [];
}

export function normalizePhone(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) return '';

  const hasPlusPrefix = trimmed.startsWith('+');
  const digitsOnly = trimmed.replace(/\D/g, '');

  return hasPlusPrefix ? `+${digitsOnly}` : `+${digitsOnly}`;
}

export function validatePhone(value: string): string | null {
  const normalized = normalizePhone(value);

  if (!normalized) return 'El telefono es obligatorio.';
  if (!/^\+[1-9]\d{7,14}$/.test(normalized)) {
    return 'Ingresa un telefono valido en formato internacional. Ej: +54 9 351 123 4567';
  }

  return null;
}

export function buildExternalId(params: {
  type: string;
  provider: string;
  name: string;
  phone: string;
  existingExternalId?: string;
}) {
  const { type, provider, name, phone, existingExternalId } = params;

  if (type === 'whatsapp') {
    return normalizePhone(phone);
  }

  if (existingExternalId?.trim()) return existingExternalId;

  const normalizedName = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'canal';

  return `${type}_${provider}_${normalizedName}`;
}

export function isKnownChannelType(value: string): value is ChannelType {
  return CHANNEL_TYPE_DEFINITIONS.some((item) => item.value === value);
}

