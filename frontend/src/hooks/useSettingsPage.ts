import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import { useTenantContext } from '@/context/tenant-context';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { getToken } from '@/services/auth';
import { getChannelConfigStatus, updateChannelConfig } from '@/services/channelConfig';
import { getChannelConfigBundle, getChannels } from '@/services/channels';
import { updateTenant } from '@/services/tenants';
import { isAllowedTenantTimezone, resolveTenantTimezone } from '@/constants/timezones';
import type {
  BotActionConfig,
  BotConfigEditable,
  BotObjectiveConfig,
  ChannelConfigValidationStatus,
  DataCollectionField,
} from '@/types/channelConfig';
import type { Channel } from '@/types/channel';
import type { ChannelSettingsEditable, TenantSettingsEditable, UserTypesEditable } from '@/types/settings';

const LAST_CHANNEL_STORAGE_KEY = 'configuracion_last_channel_id';

const emptyConfig: BotConfigEditable = {
  identity: { role: '', bot_name: '', industry: '', language: '', description: '' },
  tone: { tone: '', style_rules: [] },
  rules: { rules: [], fallback_message: '' },
  actions: [],
  objectives: [],
  data_collection: { fields: [] },
};

const emptyChannelSettings: ChannelSettingsEditable = {
  max_bot_messages: 20,
  max_bot_messages_message: '',
  human_handoff_reset_hours: 24,
  unsupported_content_message: '',
};

const emptyUserTypes: UserTypesEditable = { default_type: '', types: [] };

const emptyTenantSettings: TenantSettingsEditable = {
  name: '',
  timezone: resolveTenantTimezone(undefined),
  industry: '',
  language: 'es',
  logoUrl: '',
};

type ToastApi = {
  success: (message: string) => void;
  error: (message: string) => void;
};

function sanitizeEditableConfig(raw: Record<string, unknown> | undefined): BotConfigEditable {
  const identity = (raw?.identity as Record<string, unknown>) || {};
  const tone = (raw?.tone as Record<string, unknown>) || {};
  const rules = (raw?.rules as Record<string, unknown>) || {};
  const actions = Array.isArray(raw?.actions) ? raw.actions : [];
  const objectives = Array.isArray(raw?.objectives) ? raw.objectives : [];
  const dataCollection = raw?.data_collection;
  const fields = Array.isArray((dataCollection as Record<string, unknown>)?.fields)
    ? ((dataCollection as Record<string, unknown>).fields as unknown[])
    : Array.isArray(dataCollection)
      ? (dataCollection as unknown[])
      : [];

  return {
    identity: {
      role: typeof identity.role === 'string' ? identity.role : '',
      bot_name: typeof identity.bot_name === 'string' ? identity.bot_name : '',
      industry: typeof identity.industry === 'string' ? identity.industry : '',
      language: typeof identity.language === 'string' ? identity.language : '',
      description: typeof identity.description === 'string' ? identity.description : '',
    },
    tone: {
      tone: typeof tone.tone === 'string' ? tone.tone : '',
      style_rules: Array.isArray(tone.style_rules) ? tone.style_rules.filter((item): item is string => typeof item === 'string') : [],
    },
    rules: {
      rules: Array.isArray(rules.rules) ? rules.rules.filter((item): item is string => typeof item === 'string') : [],
      fallback_message: typeof rules.fallback_message === 'string' ? rules.fallback_message : '',
    },
    actions: actions.map((item) => {
      const value = item as Record<string, unknown>;
      return { name: typeof value?.name === 'string' ? value.name : '', description: typeof value?.description === 'string' ? value.description : '' };
    }),
    objectives: objectives.map((item) => {
      const value = item as Record<string, unknown>;
      return {
        description: typeof value?.description === 'string' ? value.description : '',
        cta_message: typeof value?.cta_message === 'string' ? value.cta_message : '',
        applies_to: Array.isArray(value?.applies_to) ? value.applies_to.filter((v): v is string => typeof v === 'string') : [],
        conversation_flow: Array.isArray(value?.conversation_flow) ? value.conversation_flow.filter((v): v is string => typeof v === 'string') : [],
      };
    }),
    data_collection: {
      fields: fields.map((item) => {
        const value = item as Record<string, unknown>;
        return { name: typeof value?.name === 'string' ? value.name : '', type: typeof value?.type === 'string' ? value.type : '' };
      }),
    },
  };
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
  const { activeTenant, refresh } = useTenantContext();
  const channelIdFromQuery = typeof router.query.id === 'string' ? router.query.id : '';
  const hasToken = Boolean(getToken());

  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);

  const [loadingChannelConfig, setLoadingChannelConfig] = useState(false);
  const [savingChannelConfig, setSavingChannelConfig] = useState(false);
  const [savingTenantSettings, setSavingTenantSettings] = useState(false);

  const [channelConfigId, setChannelConfigId] = useState('');
  const [channelConfig, setChannelConfig] = useState<BotConfigEditable>(emptyConfig);
  const [channelSettings, setChannelSettings] = useState<ChannelSettingsEditable>(emptyChannelSettings);
  const [userTypes, setUserTypes] = useState<UserTypesEditable>(emptyUserTypes);
  const [status, setStatus] = useState<ChannelConfigValidationStatus>({ is_valid: false, missing_fields: [] });

  const [tenantSettings, setTenantSettings] = useState<TenantSettingsEditable>(emptyTenantSettings);

  const [isChannelDirty, setIsChannelDirty] = useState(false);
  const [isTenantDirty, setIsTenantDirty] = useState(false);

  const loadedChannelRef = useRef<string | null>(null);

  useEffect(() => {
    setTenantSettings({
      name: activeTenant?.name ?? '',
      timezone: resolveTenantTimezone(activeTenant?.timezone),
      industry: activeTenant?.industry ?? '',
      language: typeof activeTenant?.branding_jsonb?.language === 'string' ? String(activeTenant.branding_jsonb.language) : 'es',
      logoUrl: typeof activeTenant?.branding_jsonb?.logoUrl === 'string' ? String(activeTenant.branding_jsonb.logoUrl) : '',
    });
    setIsTenantDirty(false);
  }, [activeTenant]);

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

  useEffect(() => {
    if (!hasToken) return;
    void fetchChannels();
  }, [fetchChannels, hasToken]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      setSelectedChannelId(null);
      loadedChannelRef.current = null;
      void fetchChannels();
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [fetchChannels]);

  useEffect(() => {
    if (!channels.length) {
      setSelectedChannelId(null);
      return;
    }
    const channelIds = new Set(channels.map((channel) => channel.id));
    const storedChannelId = typeof window !== 'undefined' ? window.localStorage.getItem(LAST_CHANNEL_STORAGE_KEY) : null;
    const preferredChannelId =
      (channelIdFromQuery && channelIds.has(channelIdFromQuery) ? channelIdFromQuery : null) ??
      (storedChannelId && channelIds.has(storedChannelId) ? storedChannelId : null) ??
      channels[0].id;
    setSelectedChannelId((current) => current ?? preferredChannelId);
  }, [channelIdFromQuery, channels]);

  useEffect(() => {
    if (!selectedChannelId) return;
    if (typeof window !== 'undefined') window.localStorage.setItem(LAST_CHANNEL_STORAGE_KEY, selectedChannelId);
    if (channelIdFromQuery !== selectedChannelId) void router.replace(`/configuracion?id=${selectedChannelId}`, undefined, { shallow: true });
  }, [channelIdFromQuery, router, selectedChannelId]);

  useEffect(() => {
    if (!selectedChannelId || !hasToken) return;
    if (loadedChannelRef.current === selectedChannelId) return;
    loadedChannelRef.current = selectedChannelId;

    const load = async () => {
      setLoadingChannelConfig(true);
      try {
        const configResponse = await getChannelConfigBundle(selectedChannelId);
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
  }, [hasToken, selectedChannelId, toast]);

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

  const missingFields = useMemo(() => {
    const missing: string[] = [];
    if (!channelConfig.identity?.bot_name?.trim()) missing.push('Nombre del bot');
    if (!channelConfig.tone?.tone?.trim()) missing.push('Tono');
    if (!channelConfig.rules?.rules?.length) missing.push('Reglas de comportamiento');
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

  const saveTenant = useCallback(async () => {
    if (!activeTenant?.id || savingTenantSettings) return;
    if (!tenantSettings.timezone || !isAllowedTenantTimezone(tenantSettings.timezone)) {
      toast.error('Selecciona una zona horaria valida para el negocio.');
      return;
    }
    setSavingTenantSettings(true);
    try {
      await updateTenant(activeTenant.id, {
        name: tenantSettings.name,
        timezone: tenantSettings.timezone,
        industry: tenantSettings.industry || undefined,
      });
      await refresh();
      setIsTenantDirty(false);
      toast.success('Configuracion general guardada.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo guardar la configuracion general.'));
    } finally {
      setSavingTenantSettings(false);
    }
  }, [activeTenant?.id, refresh, savingTenantSettings, tenantSettings.industry, tenantSettings.name, tenantSettings.timezone, toast]);

  const saveChannel = useCallback(async () => {
    if (!channelConfigId || !selectedChannelId || savingChannelConfig) return;
    setSavingChannelConfig(true);
    try {
      await updateChannelConfig(channelConfigId, {
        config_jsonb: channelConfig as unknown as Record<string, unknown>,
        settings_jsonb: channelSettings as unknown as Record<string, unknown>,
        user_types_jsonb: userTypes as unknown as Record<string, unknown>,
        channel_ids: [selectedChannelId],
      });
      setStatus(await getChannelConfigStatus(channelConfigId));
      setIsChannelDirty(false);
      toast.success('Configuracion del canal guardada.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo guardar la configuracion del canal.'));
    } finally {
      setSavingChannelConfig(false);
    }
  }, [channelConfig, channelConfigId, channelSettings, savingChannelConfig, selectedChannelId, toast, userTypes]);

  const updateConfigState = useCallback((next: BotConfigEditable) => {
    setChannelConfig(next);
    setIsChannelDirty(true);
  }, []);

  const updateTenantSettings = useCallback((patch: Partial<TenantSettingsEditable>) => {
    setTenantSettings((prev) => {
      const nextPatch = { ...patch };
      if (typeof nextPatch.timezone === 'string') {
        nextPatch.timezone = resolveTenantTimezone(nextPatch.timezone);
      }
      return { ...prev, ...nextPatch };
    });
    setIsTenantDirty(true);
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
    () => channels.map((channel) => ({ value: channel.id, label: `${channel.name} (${channel.type})` })),
    [channels],
  );

  return {
    hasToken,
    channels,
    channelOptions,
    channelsLoading,
    selectedChannel,
    selectedChannelId,
    loadingChannelConfig,
    savingChannelConfig,
    savingTenantSettings,
    channelConfig,
    channelSettings,
    userTypes,
    tenantSettings,
    status,
    missingFields,
    isChannelDirty,
    isTenantDirty,
    updateConfigState,
    updateChannelSettings,
    updateUserTypes,
    updateTenantSettings,
    handleChannelChange,
    saveChannel,
    saveTenant,
  };
}

export type SettingsPageHook = ReturnType<typeof useSettingsPage>;
export type { BotActionConfig, BotObjectiveConfig, DataCollectionField };
