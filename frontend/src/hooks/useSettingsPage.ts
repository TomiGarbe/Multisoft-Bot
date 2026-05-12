import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import { useTenantContext } from '@/context/tenant-context';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { getToken } from '@/services/auth';
import { getChannelConfigStatus, updateChannelConfig } from '@/services/channelConfig';
import { getChannelBotConfigActions, replaceChannelBotConfigActions } from '@/services/channelBotConfigActions';
import { getChannelConfigBundle, getChannels } from '@/services/channels';
import { getIntegrations } from '@/services/integrations';
import { createApiKey, listApiKeys, revokeApiKey } from '@/services/apiKeys';
import type {
  BotConfigEditable,
  ChannelConfigValidationStatus,
  ConfigSection,
  CustomFieldConfig,
} from '@/types/channelConfig';
import type { Channel } from '@/types/channel';
import type { ApiKeyCreatedItem, ApiKeyItem } from '@/types/apiKey';
import type { IntegrationListItem } from '@/types/integration';
import type { ChannelSettingsEditable, UserTypesEditable } from '@/types/settings';

const LAST_CHANNEL_STORAGE_KEY = 'configuracion_last_channel_id';
const ALL_CHANNELS_SCOPE = '__all_channels__';

const emptyConfig: BotConfigEditable = {
  version: 1,
  sections: [],
};

const emptyChannelSettings: ChannelSettingsEditable = {
  max_bot_messages: 20,
  max_bot_messages_message: '',
  human_handoff_reset_hours: 24,
  unsupported_content_message: '',
};

const emptyUserTypes: UserTypesEditable = { default_type: '', types: [] };

function getSection(config: Record<string, unknown> | undefined, sectionId: string): ConfigSection | null {
  const sections = config?.sections;
  if (!Array.isArray(sections)) return null;
  const match = sections.find(
    (item) => typeof item === 'object' && item !== null && (item as Record<string, unknown>).id === sectionId,
  );
  return (match as ConfigSection) ?? null;
}

function toStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function sanitizeCustomField(raw: unknown): CustomFieldConfig {
  const value = raw as Record<string, unknown>;
  return {
    key: typeof value?.key === 'string' ? value.key : '',
    label: typeof value?.label === 'string' ? value.label : '',
    type: value?.type === 'short_text' || value?.type === 'long_text' || value?.type === 'list' || value?.type === 'group' || value?.type === 'group_list'
      ? value.type
      : 'short_text',
    description: typeof value?.description === 'string' ? value.description : '',
    required: Boolean(value?.required),
    options: toStringArray(value?.options),
    fields: Array.isArray(value?.fields) ? value.fields.map(sanitizeCustomField) : [],
    item_fields: Array.isArray(value?.item_fields) ? value.item_fields.map(sanitizeCustomField) : [],
    notes: toStringArray(value?.notes),
  };
}

type ToastApi = {
  success: (message: string) => void;
  error: (message: string) => void;
};

function sanitizeEditableConfig(raw: Record<string, unknown> | undefined): BotConfigEditable {
  const sectionsRaw = Array.isArray(raw?.sections) ? raw.sections : [];
  const sections: ConfigSection[] = sectionsRaw
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((section) => {
      const entries = Array.isArray(section.entries)
        ? section.entries
          .filter((entry): entry is Record<string, unknown> => typeof entry === 'object' && entry !== null)
          .map((entry) => ({
            ...entry,
            custom_fields: Array.isArray(entry.custom_fields) ? entry.custom_fields.map(sanitizeCustomField) : [],
            notes: typeof entry.notes === 'string' ? entry.notes : '',
          }))
        : undefined;
      return {
        ...section,
        id: typeof section.id === 'string' ? section.id : '',
        type: typeof section.type === 'string' ? section.type : '',
        label: typeof section.label === 'string' ? section.label : '',
        enabled: typeof section.enabled === 'boolean' ? section.enabled : true,
        priority: typeof section.priority === 'number' ? section.priority : 0,
        fields: typeof section.fields === 'object' && section.fields !== null ? section.fields as Record<string, unknown> : undefined,
        entries,
        custom_fields: Array.isArray(section.custom_fields) ? section.custom_fields.map(sanitizeCustomField) : [],
        notes: typeof section.notes === 'string' ? section.notes : '',
      };
    });
  return {
    version: typeof raw?.version === 'number' ? raw.version : 1,
    sections,
  };
}

function buildConfigDocument(_baseConfig: Record<string, unknown> | undefined, config: BotConfigEditable): Record<string, unknown> {
  return config as unknown as Record<string, unknown>;
}

const sanitizeChannelSettings = (raw: Record<string, unknown> | undefined): ChannelSettingsEditable => ({
  max_bot_messages: typeof raw?.max_bot_messages === 'number' ? raw.max_bot_messages : 20,
  max_bot_messages_message: typeof raw?.max_bot_messages_message === 'string' ? raw.max_bot_messages_message : '',
  human_handoff_reset_hours: typeof raw?.human_handoff_reset_hours === 'number' ? raw.human_handoff_reset_hours : 24,
  unsupported_content_message: typeof raw?.unsupported_content_message === 'string' ? raw.unsupported_content_message : '',
});

function sanitizeUserTypes(raw: Record<string, unknown> | undefined): UserTypesEditable {
  const typesRaw = Array.isArray(raw?.types) ? raw.types : [];
  const types = typesRaw.map((item, index) => {
    const value = item as Record<string, unknown>;
    const key = typeof value?.key === 'string' && value.key.trim() ? value.key : `type_${index + 1}`;
    return { key, label: typeof value?.label === 'string' ? value.label : '', color: typeof value?.color === 'string' ? value.color : '#2563eb', is_default: Boolean(value?.is_default) };
  });
  return { default_type: typeof raw?.default_type === 'string' ? raw.default_type : '', types };
}

export function useSettingsPage(toast: ToastApi) {
  const router = useRouter();
  const { activeTenant, refresh, user } = useTenantContext();
  const channelIdFromQuery = typeof router.query.id === 'string' ? router.query.id : '';
  const hasToken = Boolean(getToken());
  const permissionSet = useMemo(() => new Set((user?.permissions ?? []).map((p) => p.code)), [user?.permissions]);
  const canReadIntegrations = permissionSet.has('bot_actions.read');
  const canUpdateIntegrations = permissionSet.has('channel_config.update');

  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);

  const [loadingChannelConfig, setLoadingChannelConfig] = useState(false);
  const [savingChannelConfig, setSavingChannelConfig] = useState(false);

  const [channelConfigId, setChannelConfigId] = useState('');
  const [channelConfig, setChannelConfig] = useState<BotConfigEditable>(emptyConfig);
  const [channelConfigDocument, setChannelConfigDocument] = useState<Record<string, unknown> | undefined>(undefined);
  const [channelSettings, setChannelSettings] = useState<ChannelSettingsEditable>(emptyChannelSettings);
  const [userTypes, setUserTypes] = useState<UserTypesEditable>(emptyUserTypes);
  const [status, setStatus] = useState<ChannelConfigValidationStatus>({ is_valid: false, missing_fields: [] });

  const [isChannelDirty, setIsChannelDirty] = useState(false);

  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [apiKeysLoading, setApiKeysLoading] = useState(false);
  const [apiKeysSaving, setApiKeysSaving] = useState(false);
  const [integrations, setIntegrations] = useState<IntegrationListItem[]>([]);
  const [integrationsLoading, setIntegrationsLoading] = useState(false);
  const [integrationsSaving, setIntegrationsSaving] = useState(false);
  const [selectedIntegrationIds, setSelectedIntegrationIds] = useState<Set<string>>(new Set());
  const [mixedIntegrationIds, setMixedIntegrationIds] = useState<Set<string>>(new Set());
  const [isIntegrationsDirty, setIsIntegrationsDirty] = useState(false);

  const loadedChannelRef = useRef<string | null>(null);

  useEffect(() => {
    if (!hasToken) router.replace('/login');
  }, [hasToken, router]);

  const fetchChannels = useCallback(async () => {
    setChannelsLoading(true);
    try {
      const nextChannels = await getChannels();
      setChannels(nextChannels);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo cargar la lista de canales.'));
    } finally {
      setChannelsLoading(false);
    }
  }, [toast]);

  const fetchApiKeys = useCallback(async () => {
    setApiKeysLoading(true);
    try {
      setApiKeys(await listApiKeys());
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo cargar las API keys.'));
    } finally {
      setApiKeysLoading(false);
    }
  }, [toast]);

  const fetchIntegrations = useCallback(async () => {
    if (!canReadIntegrations) {
      setIntegrations([]);
      return;
    }
    setIntegrationsLoading(true);
    try {
      setIntegrations(await getIntegrations());
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo cargar integraciones.'));
    } finally {
      setIntegrationsLoading(false);
    }
  }, [canReadIntegrations, toast]);

  useEffect(() => {
    if (!hasToken) return;
    void Promise.all([fetchChannels(), fetchApiKeys(), fetchIntegrations()]);
  }, [fetchApiKeys, fetchChannels, fetchIntegrations, hasToken]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      setSelectedChannelId(null);
      loadedChannelRef.current = null;
      setIsIntegrationsDirty(false);
      void Promise.all([fetchChannels(), fetchApiKeys(), fetchIntegrations()]);
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [fetchApiKeys, fetchChannels, fetchIntegrations]);

  useEffect(() => {
    if (!channels.length) {
      setSelectedChannelId(null);
      return;
    }
    const channelIds = new Set(channels.map((channel) => channel.id));
    const storedChannelId = typeof window !== 'undefined' ? window.localStorage.getItem(LAST_CHANNEL_STORAGE_KEY) : null;
    const preferredChannelId =
      (channelIdFromQuery === ALL_CHANNELS_SCOPE ? ALL_CHANNELS_SCOPE : null) ??
      (channelIdFromQuery && channelIds.has(channelIdFromQuery) ? channelIdFromQuery : null) ??
      (storedChannelId === ALL_CHANNELS_SCOPE ? ALL_CHANNELS_SCOPE : null) ??
      (storedChannelId && channelIds.has(storedChannelId) ? storedChannelId : null) ??
      ALL_CHANNELS_SCOPE;
    setSelectedChannelId((current) => current ?? preferredChannelId);
  }, [channelIdFromQuery, channels]);

  useEffect(() => {
    if (!selectedChannelId) return;
    if (typeof window !== 'undefined') window.localStorage.setItem(LAST_CHANNEL_STORAGE_KEY, selectedChannelId);
    if (channelIdFromQuery !== selectedChannelId) void router.replace(`/configuracion?id=${selectedChannelId}`, undefined, { shallow: true });
  }, [channelIdFromQuery, router, selectedChannelId]);

  const effectiveChannelId = useMemo(() => {
    if (!channels.length) return null;
    if (!selectedChannelId || selectedChannelId === ALL_CHANNELS_SCOPE) return channels[0].id;
    return selectedChannelId;
  }, [channels, selectedChannelId]);

  useEffect(() => {
    if (!effectiveChannelId || !hasToken) return;
    const loadRef = `${selectedChannelId ?? ''}:${effectiveChannelId}`;
    if (loadedChannelRef.current === loadRef) return;
    loadedChannelRef.current = loadRef;

    const load = async () => {
      setLoadingChannelConfig(true);
      try {
        const configResponse = await getChannelConfigBundle(effectiveChannelId);
        setChannelConfigDocument(configResponse.config);
        setChannelConfig(sanitizeEditableConfig(configResponse.config));
        setChannelSettings(sanitizeChannelSettings(configResponse.settings));
        setUserTypes(sanitizeUserTypes(configResponse.user_types));

        const maybeSettings = configResponse.settings as Record<string, unknown> | undefined;
        const maybeConfig = configResponse.config as Record<string, unknown> | undefined;
        const resolvedConfigId =
          (typeof maybeSettings?.channel_config_id === 'string' && maybeSettings.channel_config_id) ||
          (typeof maybeSettings?.config_id === 'string' && maybeSettings.config_id) ||
          (typeof maybeConfig?.id === 'string' && maybeConfig.id) ||
          '';

        setChannelConfigId(resolvedConfigId);
        if (resolvedConfigId) {
          setStatus(await getChannelConfigStatus(resolvedConfigId));
        } else {
          setStatus({ is_valid: false, missing_fields: [] });
        }
        setIsChannelDirty(false);
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'No se pudo cargar la configuracion del canal.'));
      } finally {
        setLoadingChannelConfig(false);
      }
    };

    void load();
  }, [effectiveChannelId, hasToken, selectedChannelId, toast]);

  useEffect(() => {
    if (!hasToken || !canReadIntegrations || !channels.length) return;

    const resolveConfigId = async (channelId: string): Promise<string> => {
      const bundle = await getChannelConfigBundle(channelId);
      const settings = bundle.settings as Record<string, unknown>;
      const configId = settings.config_id;
      return typeof configId === 'string' ? configId : '';
    };

    const loadIntegrationScope = async () => {
      setIntegrationsLoading(true);
      try {
        if (!selectedChannelId || selectedChannelId === ALL_CHANNELS_SCOPE) {
          const configEntries = await Promise.all(
            channels.map(async (channel) => {
              const configId = await resolveConfigId(channel.id);
              const actions = configId ? await getChannelBotConfigActions(configId) : [];
              return { configId, actionIds: new Set(actions.map((action) => action.id)) };
            }),
          );
          const counts = new Map<string, number>();
          for (const entry of configEntries) {
            for (const actionId of entry.actionIds) {
              counts.set(actionId, (counts.get(actionId) ?? 0) + 1);
            }
          }
          const selected = new Set<string>();
          const mixed = new Set<string>();
          for (const [actionId, count] of counts.entries()) {
            if (count === channels.length) selected.add(actionId);
            else if (count > 0) mixed.add(actionId);
          }
          setSelectedIntegrationIds(selected);
          setMixedIntegrationIds(mixed);
          setIsIntegrationsDirty(false);
          return;
        }

        const configId = await resolveConfigId(selectedChannelId);
        const actions = configId ? await getChannelBotConfigActions(configId) : [];
        setSelectedIntegrationIds(new Set(actions.map((action) => action.id)));
        setMixedIntegrationIds(new Set());
        setIsIntegrationsDirty(false);
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'No se pudo cargar integraciones por canal.'));
      } finally {
        setIntegrationsLoading(false);
      }
    };

    void loadIntegrationScope();
  }, [canReadIntegrations, channels, hasToken, selectedChannelId, toast]);

  useEffect(() => {
    if (!isChannelDirty) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [isChannelDirty]);

  const selectedChannel = useMemo(
    () => channels.find((channel) => channel.id === selectedChannelId) ?? null,
    [channels, selectedChannelId],
  );

  const isAllChannelsSelected = selectedChannelId === ALL_CHANNELS_SCOPE;

  const missingFields = useMemo(() => {
    const identityFields = (getSection(channelConfig as unknown as Record<string, unknown>, 'identity')?.fields ?? {}) as Record<string, unknown>;
    const toneFields = (getSection(channelConfig as unknown as Record<string, unknown>, 'tone')?.fields ?? {}) as Record<string, unknown>;
    const rulesFields = (getSection(channelConfig as unknown as Record<string, unknown>, 'rules')?.fields ?? {}) as Record<string, unknown>;
    const globalRules = toStringArray(rulesFields.global_rules);
    const businessRules = toStringArray(rulesFields.business_rules);
    const safetyRules = toStringArray(rulesFields.safety_rules);
    const missing: string[] = [];
    if (!(typeof identityFields.bot_name === 'string' && identityFields.bot_name.trim())) missing.push('Nombre del bot');
    if (!(typeof toneFields.tone === 'string' && toneFields.tone.trim())) missing.push('Tono');
    if (!globalRules.length && !businessRules.length && !safetyRules.length) missing.push('Reglas de comportamiento');
    return missing;
  }, [channelConfig]);

  const handleChannelChange = useCallback(
    (nextChannelId: string) => {
      if (!nextChannelId || nextChannelId === selectedChannelId) return;
      if (isChannelDirty) {
        const shouldDiscard = window.confirm('Tenes cambios sin guardar. Si cambias de canal se van a perder. Queres continuar?');
        if (!shouldDiscard) return;
      }
      loadedChannelRef.current = null;
      setSelectedChannelId(nextChannelId);
    },
    [isChannelDirty, selectedChannelId],
  );

  const saveChannel = useCallback(async () => {
    if (!channelConfigId || !effectiveChannelId || savingChannelConfig) return;
    setSavingChannelConfig(true);
    try {
      await updateChannelConfig(channelConfigId, {
        config_jsonb: buildConfigDocument(channelConfigDocument, channelConfig),
        settings_jsonb: channelSettings as unknown as Record<string, unknown>,
        user_types_jsonb: userTypes as unknown as Record<string, unknown>,
        channel_ids: isAllChannelsSelected ? channels.map((channel) => channel.id) : [effectiveChannelId],
      });
      setStatus(await getChannelConfigStatus(channelConfigId));
      setIsChannelDirty(false);
      toast.success(isAllChannelsSelected ? 'Configuracion guardada para todos los canales.' : 'Configuracion del canal guardada.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo guardar la configuracion del canal.'));
    } finally {
      setSavingChannelConfig(false);
    }
  }, [channelConfig, channelConfigDocument, channelConfigId, channelSettings, channels, effectiveChannelId, isAllChannelsSelected, savingChannelConfig, toast, userTypes]);

  const toggleIntegration = useCallback((actionId: string) => {
    setSelectedIntegrationIds((prev) => {
      const next = new Set(prev);
      if (next.has(actionId)) next.delete(actionId);
      else next.add(actionId);
      return next;
    });
    setMixedIntegrationIds((prev) => {
      if (!prev.has(actionId)) return prev;
      const next = new Set(prev);
      next.delete(actionId);
      return next;
    });
    setIsIntegrationsDirty(true);
  }, []);

  const saveIntegrations = useCallback(async () => {
    if (!canUpdateIntegrations || integrationsSaving || !channels.length) return;
    setIntegrationsSaving(true);
    try {
      const selectedIds = Array.from(selectedIntegrationIds);

      const resolveConfigId = async (channelId: string): Promise<string> => {
        const bundle = await getChannelConfigBundle(channelId);
        const settings = bundle.settings as Record<string, unknown>;
        const configId = settings.config_id;
        return typeof configId === 'string' ? configId : '';
      };

      const targetChannelIds =
        selectedChannelId && selectedChannelId !== ALL_CHANNELS_SCOPE
          ? [selectedChannelId]
          : channels.map((channel) => channel.id);

      await Promise.all(
        targetChannelIds.map(async (targetChannelId) => {
          const configId = await resolveConfigId(targetChannelId);
          if (!configId) return;
          await replaceChannelBotConfigActions(configId, selectedIds);
        }),
      );

      setIsIntegrationsDirty(false);
      toast.success(
        selectedChannelId === ALL_CHANNELS_SCOPE || !selectedChannelId
          ? 'Integraciones guardadas para todos los canales.'
          : 'Integraciones guardadas para el canal.',
      );
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo guardar integraciones.'));
    } finally {
      setIntegrationsSaving(false);
    }
  }, [canUpdateIntegrations, integrationsSaving, channels, selectedIntegrationIds, selectedChannelId, toast]);

  const createWebhookApiKey = useCallback(async (payload: { name: string; channelId?: string; expiresAt?: string }) => {
    if (!activeTenant?.id || apiKeysSaving) return null;
    setApiKeysSaving(true);
    try {
      const created = await createApiKey({
        tenant_id: activeTenant.id,
        channel_id: payload.channelId,
        name: payload.name,
        expires_at: payload.expiresAt,
      });
      await fetchApiKeys();
      toast.success('API key creada. Guardala porque no se mostrara otra vez.');
      return created;
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo crear la API key.'));
      return null;
    } finally {
      setApiKeysSaving(false);
    }
  }, [activeTenant?.id, apiKeysSaving, fetchApiKeys, toast]);

  const deactivateWebhookApiKey = useCallback(async (apiKeyId: string) => {
    if (apiKeysSaving) return;
    setApiKeysSaving(true);
    try {
      await revokeApiKey(apiKeyId);
      await fetchApiKeys();
      toast.success('API key desactivada.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo desactivar la API key.'));
    } finally {
      setApiKeysSaving(false);
    }
  }, [apiKeysSaving, fetchApiKeys, toast]);

  const regenerateWebhookApiKey = useCallback(async (apiKey: ApiKeyItem): Promise<ApiKeyCreatedItem | null> => {
    if (apiKeysSaving) return null;
    setApiKeysSaving(true);
    try {
      const created = await createApiKey({
        tenant_id: apiKey.tenant_id,
        channel_id: apiKey.channel_id ?? undefined,
        name: `${apiKey.name} regenerated`,
      });
      await revokeApiKey(apiKey.id);
      await fetchApiKeys();
      toast.success('API key regenerada y key anterior desactivada.');
      return created;
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo regenerar la API key.'));
      return null;
    } finally {
      setApiKeysSaving(false);
    }
  }, [apiKeysSaving, fetchApiKeys, toast]);

  const deleteWebhookApiKey = useCallback(async (apiKeyId: string) => {
    await deactivateWebhookApiKey(apiKeyId);
  }, [deactivateWebhookApiKey]);

  const updateConfigState = useCallback((next: BotConfigEditable) => {
    setChannelConfig(next);
    setIsChannelDirty(true);
  }, []);

  const updateChannelSettings = useCallback((patch: Partial<ChannelSettingsEditable>) => {
    setChannelSettings((prev) => ({ ...prev, ...patch }));
    setIsChannelDirty(true);
  }, []);

  const updateUserTypes = useCallback((next: UserTypesEditable) => {
    setUserTypes(next);
    setIsChannelDirty(true);
  }, []);

  const channelOptions = useMemo(
    () => [
      { value: ALL_CHANNELS_SCOPE, label: 'Todos los canales' },
      ...channels.map((channel) => ({ value: channel.id, label: `${channel.name} (${channel.type})` })),
    ],
    [channels],
  );

  return {
    hasToken,
    channels,
    channelOptions,
    channelsLoading,
    selectedChannel,
    selectedChannelId,
    effectiveChannelId,
    isAllChannelsSelected,
    loadingChannelConfig,
    savingChannelConfig,
    channelConfig,
    channelSettings,
    userTypes,
    status,
    missingFields,
    isChannelDirty,
    apiKeys,
    apiKeysLoading,
    apiKeysSaving,
    integrations,
    integrationsLoading,
    integrationsSaving,
    selectedIntegrationIds,
    mixedIntegrationIds,
    isIntegrationsDirty,
    canReadIntegrations,
    canUpdateIntegrations,
    updateConfigState,
    updateChannelSettings,
    updateUserTypes,
    handleChannelChange,
    saveChannel,
    toggleIntegration,
    saveIntegrations,
    createWebhookApiKey,
    deactivateWebhookApiKey,
    regenerateWebhookApiKey,
    deleteWebhookApiKey,
  };
}

export type SettingsPageHook = ReturnType<typeof useSettingsPage>;
