import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { getApiErrorMessage } from '@/services/api';
import { getToken } from '@/services/auth';
import { getChannelConfigStatus, updateChannelConfig } from '@/services/channelConfig';
import { getChannelConfigBundle, getChannels } from '@/services/channels';
import type { Channel } from '@/types/channel';
import type { BotActionConfig, BotConfigEditable, BotObjectiveConfig, ChannelConfigValidationStatus, DataCollectionField } from '@/types/channelConfig';

type UserTypeItem = { key: string; label: string; color: string; is_default: boolean };
type UserTypesEditable = { default_type: string; types: UserTypeItem[] };
type SettingsEditable = {
  max_bot_messages: number;
  max_bot_messages_message: string;
  human_handoff_reset_hours: number;
  unsupported_content_message: string;
};

const emptyConfig: BotConfigEditable = {
  identity: { role: '', bot_name: '', industry: '', language: '', description: '' },
  tone: { tone: '', style_rules: [] },
  rules: { rules: [], fallback_message: '' },
  actions: [],
  objectives: [],
  data_collection: { fields: [] },
};
const emptySettings: SettingsEditable = { max_bot_messages: 20, max_bot_messages_message: '', human_handoff_reset_hours: 24, unsupported_content_message: '' };
const emptyUserTypes: UserTypesEditable = { default_type: '', types: [] };
const LAST_CHANNEL_STORAGE_KEY = 'configuracion_last_channel_id';

function getMissingFields(config: BotConfigEditable) {
  const missing: string[] = [];

  if (!config.identity?.bot_name?.trim()) missing.push('Nombre del bot');
  if (!config.tone?.tone?.trim()) missing.push('Tono');
  if (!config.rules?.rules?.length) missing.push('Reglas de comportamiento');

  return missing;
}

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
    data_collection: { fields: fields.map((item) => {
      const value = item as Record<string, unknown>;
      return { name: typeof value?.name === 'string' ? value.name : '', type: typeof value?.type === 'string' ? value.type : '' };
    }) },
  };
}

const sanitizeSettings = (raw: Record<string, unknown> | undefined): SettingsEditable => ({
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

export default function ConfiguracionPage() {
  const router = useRouter();
  const toast = useToast();
  const channelIdFromQuery = typeof router.query.id === 'string' ? router.query.id : '';
  const hasToken = Boolean(getToken());
  const [channels, setChannels] = useState<Channel[]>([]);
  const [channelsLoading, setChannelsLoading] = useState(false);
  const [selectedChannelId, setSelectedChannelId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [saveModalOpen, setSaveModalOpen] = useState(false);
  const [saveMode, setSaveMode] = useState<'current' | 'multiple'>('current');
  const [selectedSaveChannelIds, setSelectedSaveChannelIds] = useState<string[]>([]);
  const [config, setConfig] = useState<BotConfigEditable>(emptyConfig);
  const [settings, setSettings] = useState<SettingsEditable>(emptySettings);
  const [userTypes, setUserTypes] = useState<UserTypesEditable>(emptyUserTypes);
  const [channelConfigId, setChannelConfigId] = useState<string>('');
  const [status, setStatus] = useState<ChannelConfigValidationStatus>({ is_valid: false, missing_fields: [] });
  const loadedChannelRef = useRef<string | null>(null);

  useEffect(() => { if (!hasToken) router.replace('/login'); }, [hasToken, router]);
  useEffect(() => {
    if (!hasToken) return;
    const loadChannels = async () => {
      setChannelsLoading(true);
      try {
        const nextChannels = await getChannels();
        setChannels(nextChannels);
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'No se pudo cargar la lista de canales.'));
      } finally {
        setChannelsLoading(false);
      }
    };
    void loadChannels();
  }, [hasToken, toast]);

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
    if (!hasToken || !selectedChannelId) return;
    if (loadedChannelRef.current === selectedChannelId) return;
    loadedChannelRef.current = selectedChannelId;
    const load = async () => {
      setLoading(true);
      try {
        const configResponse = await getChannelConfigBundle(selectedChannelId);
        setConfig(sanitizeEditableConfig(configResponse.config));
        setSettings(sanitizeSettings(configResponse.settings));
        setUserTypes(sanitizeUserTypes(configResponse.user_types));
        const maybeSettings = configResponse.settings as Record<string, unknown> | undefined;
        const maybeConfig = configResponse.config as Record<string, unknown> | undefined;
        const resolvedConfigId =
          (typeof maybeSettings?.channel_config_id === 'string' && maybeSettings.channel_config_id) ||
          (typeof maybeSettings?.config_id === 'string' && maybeSettings.config_id) ||
          (typeof maybeConfig?.id === 'string' && maybeConfig.id) || '';
        setChannelConfigId(resolvedConfigId);
        if (resolvedConfigId) setStatus(await getChannelConfigStatus(resolvedConfigId));
        setIsDirty(false);
      } catch (error) {
        toast.error(getApiErrorMessage(error, 'No se pudo cargar la configuracion del canal.'));
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [selectedChannelId, hasToken, toast]);

  useEffect(() => {
    if (!isDirty) return;
    const onBeforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', onBeforeUnload);
    return () => window.removeEventListener('beforeunload', onBeforeUnload);
  }, [isDirty]);

  if (!hasToken) return null;
  const missingFields = useMemo(() => getMissingFields(config), [config]);
  const markDirty = () => setIsDirty(true);
  const updateStringList = (list: string[], index: number, value: string) => {
    const next = [...list]; next[index] = value; return next;
  };
  const parseListInput = (value: string) => value.split(',').map((item) => item.trim()).filter(Boolean);
  const updateConfigState = (next: BotConfigEditable) => {
    setConfig(next); markDirty();
  };

  const handleChannelChange = (nextChannelId: string) => {
    if (!nextChannelId || nextChannelId === selectedChannelId) return;
    if (isDirty) {
      const shouldDiscard = window.confirm('Tenes cambios sin guardar. Si cambias de canal, se van a perder. Queres continuar?');
      if (!shouldDiscard) return;
    }
    loadedChannelRef.current = null;
    setSelectedChannelId(nextChannelId);
  };

  const openSaveModal = () => {
    if (!selectedChannelId || !channelConfigId || saving) return;
    setSaveMode('current');
    setSelectedSaveChannelIds([selectedChannelId]);
    setSaveModalOpen(true);
  };

  const saveConfig = async () => {
    if (!selectedChannelId || !channelConfigId || saving) return;
    setSaving(true);
    try {
      const channelIds = saveMode === 'multiple' ? selectedSaveChannelIds : [selectedChannelId];
      if (!channelIds.length) {
        toast.error('Selecciona al menos un canal para guardar.');
        return;
      }
      await updateChannelConfig(channelConfigId, {
        config_jsonb: config as unknown as Record<string, unknown>,
        settings_jsonb: settings as unknown as Record<string, unknown>,
        user_types_jsonb: userTypes as unknown as Record<string, unknown>,
        channel_ids: channelIds,
      });
      setStatus(await getChannelConfigStatus(channelConfigId));
      setIsDirty(false);
      setSaveModalOpen(false);
      toast.success(`Configuracion actualizada en ${channelIds.length} canal${channelIds.length === 1 ? '' : 'es'}.`);
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'No se pudo guardar la configuracion.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="config-page flex h-full min-h-0 flex-col overflow-hidden">
        <div className="config-header shrink-0 px-6 pt-6 md:px-8 md:pt-8">
          <PageHeader
            title="Configuracion"
            description="Panel completo de configuracion del bot, tipos de usuario y settings del canal."
            actions={<div className="flex items-center gap-3"><span className={`rounded-lg border px-3 py-1 text-xs font-semibold ${missingFields.length ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-emerald-200 bg-emerald-50 text-emerald-700'}`}>{missingFields.length ? 'Configuracion incompleta (opcional)' : 'Configuracion completa'}</span><Button onClick={openSaveModal} disabled={saving || !selectedChannelId || !channelConfigId}>{saving ? 'Guardando...' : 'Guardar'}</Button></div>}
          />
        </div>

        <div className="config-content min-h-0 flex-1 overflow-y-auto px-6 pb-6 pt-6 md:px-8 md:pb-8">
          <div className="space-y-6">
            <section className="rounded-xl border border-slate-200 bg-white p-4">
              <label className="mb-2 block text-sm font-medium text-slate-700">Canal</label>
              <select
                value={selectedChannelId ?? ''}
                onChange={(event) => handleChannelChange(event.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200 md:max-w-sm"
                disabled={channelsLoading || !channels.length}
              >
                {!channels.length ? <option value="">Sin canales disponibles</option> : null}
                {channels.map((channel) => <option key={channel.id} value={channel.id}>{channel.name} ({channel.type})</option>)}
              </select>
            </section>

            {channelsLoading || loading ? <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500">Cargando configuracion...</div> : null}
            {!channelsLoading && !channels.length ? <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">Este negocio no tiene canales configurados.</div> : null}
            {missingFields.length > 0 ? (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                <p className="font-medium">Configuracion incompleta (opcional)</p>
                <p className="mt-1">Podes guardar aunque falten campos.</p>
                <p className="mt-2">Falta completar: {missingFields.join(', ')}</p>
              </div>
            ) : null}

            {!loading && selectedChannelId ? <div className="space-y-6">
          <section className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">Settings</h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Input label="Maximo de mensajes del bot" value={String(settings.max_bot_messages)} onChange={(event) => { setSettings({ ...settings, max_bot_messages: Number(event.target.value) || 0 }); markDirty(); }} />
              <Input label="Horas para reset humano" value={String(settings.human_handoff_reset_hours)} onChange={(event) => { setSettings({ ...settings, human_handoff_reset_hours: Number(event.target.value) || 0 }); markDirty(); }} />
              <div className="space-y-1.5 md:col-span-2"><label className="block text-sm font-medium text-slate-700">Mensaje al derivar</label><textarea value={settings.max_bot_messages_message} onChange={(event) => { setSettings({ ...settings, max_bot_messages_message: event.target.value }); markDirty(); }} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /></div>
              <div className="space-y-1.5 md:col-span-2"><label className="block text-sm font-medium text-slate-700">Mensaje contenido no soportado</label><textarea value={settings.unsupported_content_message} onChange={(event) => { setSettings({ ...settings, unsupported_content_message: event.target.value }); markDirty(); }} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /></div>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">User Types</h2>
            <div className="space-y-3">
              {(userTypes.types?.length >= 0 ? userTypes.types : []).map((userType, index) => (
                <div key={userType.key || `user-type-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_140px_140px_auto]">
                  <Input label="Label" value={userType.label} onChange={(event) => { const next = [...userTypes.types]; next[index] = { ...next[index], label: event.target.value }; setUserTypes({ ...userTypes, types: next }); markDirty(); }} />
                  <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Color</label><input type="color" value={userType.color} onChange={(event) => { const next = [...userTypes.types]; next[index] = { ...next[index], color: event.target.value }; setUserTypes({ ...userTypes, types: next }); markDirty(); }} className="h-10 w-full rounded-lg border border-slate-300" /></div>
                  <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Default</label><Button variant={userType.is_default ? 'primary' : 'secondary'} onClick={() => { const next = userTypes.types.map((item, currentIndex) => ({ ...item, is_default: currentIndex === index })); setUserTypes({ ...userTypes, types: next, default_type: next[index].key }); markDirty(); }}>{userType.is_default ? 'Seleccionado' : 'Seleccionar'}</Button></div>
                  <div className="flex items-end"><Button variant="danger" onClick={() => { const next = userTypes.types.filter((_, currentIndex) => currentIndex !== index); setUserTypes({ ...userTypes, types: next }); markDirty(); }}>Eliminar</Button></div>
                </div>
              ))}
              <Button variant="secondary" onClick={() => { setUserTypes({ ...userTypes, types: [...userTypes.types, { key: `type_${userTypes.types.length + 1}`, label: '', color: '#2563eb', is_default: false }] }); markDirty(); }}>Agregar tipo</Button>
            </div>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
            <h2 className="mb-4 text-lg font-semibold text-slate-900">Config</h2>
            <div className="space-y-6">
              <div className="space-y-4"><h3 className="text-base font-semibold text-slate-800">Identidad</h3><div className="grid grid-cols-1 gap-4 md:grid-cols-2"><Input label="Rol" value={config.identity.role} onChange={(event) => updateConfigState({ ...config, identity: { ...config.identity, role: event.target.value } })} /><Input label="Nombre del bot" value={config.identity.bot_name} warning={!config.identity.bot_name.trim() ? 'Opcional: recomendado para completar la configuracion.' : undefined} onChange={(event) => updateConfigState({ ...config, identity: { ...config.identity, bot_name: event.target.value } })} /><Input label="Industria" value={config.identity.industry} onChange={(event) => updateConfigState({ ...config, identity: { ...config.identity, industry: event.target.value } })} /><Input label="Idioma" value={config.identity.language} onChange={(event) => updateConfigState({ ...config, identity: { ...config.identity, language: event.target.value } })} /><div className="space-y-1.5 md:col-span-2"><label className="block text-sm font-medium text-slate-700">Descripcion</label><textarea value={config.identity.description} onChange={(event) => updateConfigState({ ...config, identity: { ...config.identity, description: event.target.value } })} className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /></div></div></div>
              <div className="space-y-4"><h3 className="text-base font-semibold text-slate-800">Tono</h3><Input label="Tono" value={config.tone.tone} warning={!config.tone.tone.trim() ? 'Opcional: recomendado para definir el estilo de respuestas.' : undefined} onChange={(event) => updateConfigState({ ...config, tone: { ...config.tone, tone: event.target.value } })} /><div className="space-y-2"><div className="flex items-center justify-between"><label className="text-sm font-medium text-slate-700">Reglas de estilo</label><Button variant="secondary" onClick={() => updateConfigState({ ...config, tone: { ...config.tone, style_rules: [...config.tone.style_rules, ''] } })}>Agregar regla de estilo</Button></div>{(config.tone.style_rules?.length >= 0 ? config.tone.style_rules : []).map((item, index) => (<div key={`style-rule-${index}`} className="flex gap-2"><input value={item} onChange={(event) => updateConfigState({ ...config, tone: { ...config.tone, style_rules: updateStringList(config.tone.style_rules, index, event.target.value) } })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /><Button variant="danger" onClick={() => updateConfigState({ ...config, tone: { ...config.tone, style_rules: config.tone.style_rules.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button></div>))}</div></div>
              <div className="space-y-4"><h3 className="text-base font-semibold text-slate-800">Reglas</h3><div className="space-y-2"><div className="flex items-center justify-between"><label className="text-sm font-medium text-slate-700">Reglas</label><Button variant="secondary" onClick={() => updateConfigState({ ...config, rules: { ...config.rules, rules: [...config.rules.rules, ''] } })}>Agregar regla</Button></div>{(config.rules.rules?.length >= 0 ? config.rules.rules : []).map((rule, index) => (<div key={`rule-${index}`} className="flex gap-2"><input value={rule} onChange={(event) => updateConfigState({ ...config, rules: { ...config.rules, rules: updateStringList(config.rules.rules, index, event.target.value) } })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /><Button variant="danger" onClick={() => updateConfigState({ ...config, rules: { ...config.rules, rules: config.rules.rules.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button></div>))}</div>{!config.rules.rules.length ? <p className="text-xs text-amber-700">Opcional: agrega al menos una regla de comportamiento para mejorar la guia del bot.</p> : null}<div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Mensaje fallback</label><textarea value={config.rules.fallback_message} onChange={(event) => updateConfigState({ ...config, rules: { ...config.rules, fallback_message: event.target.value } })} className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /></div></div>
              <div className="space-y-4"><div className="flex items-center justify-between"><h3 className="text-base font-semibold text-slate-800">Acciones</h3><Button variant="secondary" onClick={() => updateConfigState({ ...config, actions: [...config.actions, { name: '', description: '' }] })}>Agregar accion</Button></div>{(config.actions?.length >= 0 ? config.actions : []).map((action: BotActionConfig, index) => (<div key={`action-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_2fr_auto]"><input placeholder="Nombre" value={action.name} onChange={(event) => { const nextActions = [...config.actions]; nextActions[index] = { ...nextActions[index], name: event.target.value }; updateConfigState({ ...config, actions: nextActions }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /><input placeholder="Descripcion" value={action.description} onChange={(event) => { const nextActions = [...config.actions]; nextActions[index] = { ...nextActions[index], description: event.target.value }; updateConfigState({ ...config, actions: nextActions }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /><Button variant="danger" onClick={() => updateConfigState({ ...config, actions: config.actions.filter((_, currentIndex) => currentIndex !== index) })}>Eliminar</Button></div>))}</div>
              <div className="space-y-4"><div className="flex items-center justify-between"><h3 className="text-base font-semibold text-slate-800">Objetivos</h3><Button variant="secondary" onClick={() => updateConfigState({ ...config, objectives: [...config.objectives, { description: '', cta_message: '', applies_to: [], conversation_flow: [] }] })}>Agregar objetivo</Button></div>{(config.objectives?.length >= 0 ? config.objectives : []).map((objective: BotObjectiveConfig, index) => (<div key={`objective-${index}`} className="space-y-3 rounded-lg border border-slate-200 p-3"><Input label="Descripcion" value={objective.description} onChange={(event) => { const nextObjectives = [...config.objectives]; nextObjectives[index] = { ...nextObjectives[index], description: event.target.value }; updateConfigState({ ...config, objectives: nextObjectives }); }} /><Input label="Mensaje CTA" value={objective.cta_message} onChange={(event) => { const nextObjectives = [...config.objectives]; nextObjectives[index] = { ...nextObjectives[index], cta_message: event.target.value }; updateConfigState({ ...config, objectives: nextObjectives }); }} /><Input label="Aplica a" value={objective.applies_to.join(', ')} onChange={(event) => { const nextObjectives = [...config.objectives]; nextObjectives[index] = { ...nextObjectives[index], applies_to: parseListInput(event.target.value) }; updateConfigState({ ...config, objectives: nextObjectives }); }} /><Input label="Flujo" value={objective.conversation_flow.join(', ')} onChange={(event) => { const nextObjectives = [...config.objectives]; nextObjectives[index] = { ...nextObjectives[index], conversation_flow: parseListInput(event.target.value) }; updateConfigState({ ...config, objectives: nextObjectives }); }} /><Button variant="danger" onClick={() => updateConfigState({ ...config, objectives: config.objectives.filter((_, currentIndex) => currentIndex !== index) })}>Eliminar objetivo</Button></div>))}</div>
              <div className="space-y-4"><div className="flex items-center justify-between"><h3 className="text-base font-semibold text-slate-800">Data Collection</h3><Button variant="secondary" onClick={() => updateConfigState({ ...config, data_collection: { fields: [...config.data_collection.fields, { name: '', type: '' }] } })}>Agregar campo</Button></div>{(config.data_collection.fields?.length >= 0 ? config.data_collection.fields : []).map((field: DataCollectionField, index) => (<div key={`field-${index}`} className="grid grid-cols-1 gap-2 md:grid-cols-[1fr_220px_auto]"><input placeholder="Nombre" value={field.name} onChange={(event) => { const nextFields = [...config.data_collection.fields]; nextFields[index] = { ...nextFields[index], name: event.target.value }; updateConfigState({ ...config, data_collection: { fields: nextFields } }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /><input placeholder="Tipo" value={field.type} onChange={(event) => { const nextFields = [...config.data_collection.fields]; nextFields[index] = { ...nextFields[index], type: event.target.value }; updateConfigState({ ...config, data_collection: { fields: nextFields } }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" /><Button variant="danger" onClick={() => updateConfigState({ ...config, data_collection: { fields: config.data_collection.fields.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button></div>))}</div>
            </div>
          </section>
            </div> : null}
          </div>
        </div>

        <Modal
          isOpen={saveModalOpen}
          title="¿Dónde querés aplicar estos cambios?"
          onClose={() => { if (!saving) setSaveModalOpen(false); }}
          footer={
            <div className="flex items-center justify-end gap-2">
              <Button variant="secondary" onClick={() => setSaveModalOpen(false)} disabled={saving}>Cancelar</Button>
              <Button onClick={() => void saveConfig()} disabled={saving}>{saving ? 'Guardando...' : 'Confirmar guardado'}</Button>
            </div>
          }
        >
          <div className="space-y-4 text-sm text-slate-700">
            <label className="flex items-center gap-2">
              <input type="radio" checked={saveMode === 'current'} onChange={() => setSaveMode('current')} />
              <span>Solo este canal</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="radio" checked={saveMode === 'multiple'} onChange={() => setSaveMode('multiple')} />
              <span>Aplicar a otros canales</span>
            </label>

            {saveMode === 'multiple' ? (
              <div className="space-y-2 rounded-lg border border-slate-200 p-3">
                {channels.map((channel) => {
                  const checked = selectedSaveChannelIds.includes(channel.id);
                  return (
                    <label key={`save-channel-${channel.id}`} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          if (event.target.checked) {
                            setSelectedSaveChannelIds((prev) => Array.from(new Set([...prev, channel.id])));
                            return;
                          }
                          setSelectedSaveChannelIds((prev) => prev.filter((id) => id !== channel.id));
                        }}
                      />
                      <span>{channel.name} ({channel.type})</span>
                    </label>
                  );
                })}
              </div>
            ) : null}
          </div>
        </Modal>
      </div>
    </AppLayout>
  );
}
