'use client';

import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import { CHANNEL_TYPE_DEFINITIONS, CHANNEL_TYPE_LABELS, type ChannelType } from '@/components/channels/channelFormConfig';
import {
  buildExternalId,
  getDynamicFields,
  getProviderOptions,
  isKnownChannelType,
  validatePhone,
} from '@/components/channels/channelFormUtils';
import { useTenantContext } from '@/context/tenant-context';
import { getApiErrorMessage } from '@/services/api';
import { createChannel, updateChannel } from '@/services/channels';
import type { Channel, ChannelCreate, ChannelUpdate } from '@/types/channel';

interface ChannelsFormProps {
  isOpen: boolean;
  channel: Channel | null;
  onClose: () => void;
  onSaved: (message: string) => void;
}

interface FormState {
  tenant_id: string;
  type: ChannelType;
  provider: string;
  name: string;
  webhook_url: string;
  phone: string;
}

const DEFAULT_TYPE: ChannelType = 'whatsapp';

const initialForm: FormState = {
  tenant_id: '',
  type: DEFAULT_TYPE,
  provider: getProviderOptions(DEFAULT_TYPE)[0]?.value ?? '',
  name: '',
  webhook_url: '',
  phone: '',
};

export default function ChannelsForm({ isOpen, channel, onClose, onSaved }: ChannelsFormProps) {
  const isEditing = Boolean(channel);
  const { tenants: allowedTenants } = useTenantContext();
  const [form, setForm] = useState<FormState>(initialForm);
  const [existingExternalId, setExistingExternalId] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const providerOptions = useMemo(() => getProviderOptions(form.type), [form.type]);
  const dynamicFields = useMemo(() => getDynamicFields(form.type, form.provider), [form.type, form.provider]);

  useEffect(() => {
    if (!providerOptions.some((option) => option.value === form.provider)) {
      setForm((prev) => ({ ...prev, provider: providerOptions[0]?.value ?? '' }));
    }
  }, [providerOptions, form.provider]);

  useEffect(() => {
    if (!isOpen) return;

    if (channel) {
      const channelType = isKnownChannelType(channel.type) ? channel.type : DEFAULT_TYPE;
      const config = channel.config || {};
      const provider = typeof config.provider === 'string' ? config.provider : getProviderOptions(channelType)[0]?.value ?? '';
      const webhookUrl = typeof config.webhook_url === 'string' ? config.webhook_url : '';

      setForm({
        tenant_id: channel.tenant_id,
        type: channelType,
        provider,
        name: channel.name,
        webhook_url: webhookUrl,
        phone: channelType === 'whatsapp' ? channel.external_id : '',
      });
      setExistingExternalId(channel.external_id);
    } else {
      setForm((prev) => ({ ...initialForm, tenant_id: prev.tenant_id || allowedTenants[0]?.id || '' }));
      setExistingExternalId('');
    }

    setError(null);
  }, [isOpen, channel, allowedTenants]);

  const phoneError = useMemo(() => {
    if (!dynamicFields.some((field) => field.key === 'phone')) return null;
    return validatePhone(form.phone);
  }, [dynamicFields, form.phone]);

  const canSubmit = useMemo(() => {
    if (!form.tenant_id || !form.name.trim() || !form.provider) return false;
    if (dynamicFields.some((field) => field.key === 'phone') && phoneError) return false;
    return !isSaving;
  }, [form.tenant_id, form.name, form.provider, dynamicFields, phoneError, isSaving]);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!form.tenant_id.trim()) {
      setError('Selecciona un negocio.');
      return;
    }

    if (!form.name.trim()) {
      setError('El nombre del canal es obligatorio.');
      return;
    }

    if (!form.provider) {
      setError('Selecciona un provider.');
      return;
    }

    if (phoneError) {
      setError(phoneError);
      return;
    }

    setError(null);
    setIsSaving(true);

    try {
      const external_id = buildExternalId({
        type: form.type,
        provider: form.provider,
        name: form.name,
        phone: form.phone,
        existingExternalId,
      });

      const config: Record<string, unknown> = {
        provider: form.provider,
      };

      if (form.webhook_url.trim()) {
        config.webhook_url = form.webhook_url.trim();
      }

      if (isEditing && channel) {
        const payload: ChannelUpdate = {
          type: form.type,
          name: form.name.trim(),
          external_id,
          config,
        };

        await updateChannel(channel.id, payload);
        onSaved('Canal actualizado correctamente.');
      } else {
        const payload: ChannelCreate = {
          tenant_id: form.tenant_id,
          type: form.type,
          name: form.name.trim(),
          external_id,
          config,
          is_active: true,
        };

        await createChannel(payload);
        onSaved('Canal creado correctamente.');
      }

      onClose();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No se pudo guardar el canal.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      title={isEditing ? 'Editar canal' : 'Crear canal'}
      onClose={() => {
        if (!isSaving) onClose();
      }}
      footer={
        <div className="flex items-center justify-end gap-3">
          <Button variant="secondary" type="button" onClick={onClose} disabled={isSaving}>
            Cancelar
          </Button>
          <Button type="submit" form="channel-form" disabled={!canSubmit}>
            {isSaving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear canal'}
          </Button>
        </div>
      }
    >
      <form id="channel-form" className="space-y-5" onSubmit={submit}>
        {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}

        <Select
          label="Negocio"
          id="channel-tenant"
          value={form.tenant_id}
          onChange={(event) => setForm((prev) => ({ ...prev, tenant_id: event.target.value }))}
          disabled={isSaving || isEditing}
          placeholder="Selecciona un negocio"
          options={allowedTenants.map((tenant) => ({ value: tenant.id, label: tenant.name }))}
          required
        />

        <Input
          label="Nombre del canal"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
          placeholder="Canal principal"
          required
          disabled={isSaving}
        />

        <Select
          label="Tipo"
          id="channel-type"
          value={form.type}
          onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value as ChannelType }))}
          disabled={isSaving || isEditing}
          options={CHANNEL_TYPE_DEFINITIONS.map((typeOption) => ({ value: typeOption.value, label: CHANNEL_TYPE_LABELS[typeOption.value] }))}
        />

        <Select
          label="Provider"
          id="channel-provider"
          value={form.provider}
          onChange={(event) => setForm((prev) => ({ ...prev, provider: event.target.value }))}
          disabled={isSaving}
          options={providerOptions.map((provider) => ({ value: provider.value, label: provider.label }))}
          required
        />

        {dynamicFields.map((field) => {
          if (field.key === 'phone') {
            return (
              <Input
                key={field.key}
                label={field.label}
                value={form.phone}
                onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
                placeholder={field.placeholder}
                required={field.required}
                error={phoneError ?? undefined}
                disabled={isSaving}
              />
            );
          }

          return null;
        })}

        <Input
          label="Webhook URL"
          value={form.webhook_url}
          onChange={(event) => setForm((prev) => ({ ...prev, webhook_url: event.target.value }))}
          placeholder="https://api.tudominio.com/webhooks/canales"
          type="url"
          disabled={isSaving}
        />
      </form>
    </Modal>
  );
}
