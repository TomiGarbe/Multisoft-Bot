'use client';

import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import Checkbox from '@/components/ui/Checkbox';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { getApiErrorMessage } from '@/services/api';
import { getTenants } from '@/services/tenants';
import { createChannel, updateChannel } from '@/services/channels';
import type { Channel, ChannelCreate, ChannelUpdate } from '@/types/channel';
import type { Tenant } from '@/types/tenant';

interface ChannelsFormProps {
  isOpen: boolean;
  channel: Channel | null;
  onClose: () => void;
  onSaved: (message: string) => void;
}

interface FormState {
  tenant_id: string;
  type: string;
  name: string;
  external_id: string;
  is_active: boolean;
  provider?: string;
  instance_id?: string;
  webhook_url?: string;
  widget_id?: string;
}

const CHANNEL_TYPES = ['whatsapp', 'web'] as const;

const initialForm: FormState = {
  tenant_id: '',
  type: 'whatsapp',
  name: '',
  external_id: '',
  is_active: true,
  provider: '',
  instance_id: '',
  webhook_url: '',
  widget_id: '',
};

export default function ChannelsForm({
  isOpen,
  channel,
  onClose,
  onSaved,
}: ChannelsFormProps) {
  const isEditing = Boolean(channel);
  const [form, setForm] = useState<FormState>(initialForm);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingTenants, setIsLoadingTenants] = useState(false);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const loadTenants = async () => {
      try {
        setIsLoadingTenants(true);
        const tenantList = await getTenants();
        setTenants(tenantList);

        if (!channel && tenantList.length > 0) {
          setForm((prev) => ({ ...prev, tenant_id: tenantList[0].id }));
        }
      } catch (err) {
        setError(getApiErrorMessage(err, 'No se pudieron cargar los negocios.'));
      } finally {
        setIsLoadingTenants(false);
      }
    };

    if (channel) {
      const config = channel.config || {};
      setForm({
        tenant_id: channel.tenant_id,
        type: channel.type,
        name: channel.name,
        external_id: channel.external_id,
        is_active: channel.is_active,
        provider: config.provider || '',
        instance_id: config.instance_id || '',
        webhook_url: config.webhook_url || '',
        widget_id: config.widget_id || '',
      });
    } else {
      setForm(initialForm);
    }

    void loadTenants();
    setError(null);
  }, [isOpen, channel]);

  const canSubmit = useMemo(
    () =>
      form.tenant_id.length > 0 &&
      form.name.trim().length > 0 &&
      form.external_id.trim().length > 0 &&
      (form.type === 'whatsapp'
        ? form.provider && form.instance_id && form.webhook_url
        : form.type === 'web'
          ? form.widget_id
          : true) &&
      !isSaving,
    [form, isSaving],
  );

  const buildConfig = (): Record<string, any> => {
    if (form.type === 'whatsapp') {
      return {
        provider: form.provider || '',
        instance_id: form.instance_id || '',
        webhook_url: form.webhook_url || '',
      };
    }
    if (form.type === 'web') {
      return {
        widget_id: form.widget_id || '',
      };
    }
    return {};
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!form.tenant_id.trim()) {
      setError('Selecciona un negocio.');
      return;
    }

    if (!form.name.trim()) {
      setError('El nombre es obligatorio.');
      return;
    }

    if (!form.external_id.trim()) {
      setError('El ID externo es obligatorio.');
      return;
    }

    if (form.type === 'whatsapp') {
      if (!form.provider || !form.instance_id || !form.webhook_url) {
        setError('Proveedor, ID de instancia y URL de webhook son obligatorios para canales de WhatsApp.');
        return;
      }
    }

    if (form.type === 'web') {
      if (!form.widget_id) {
        setError('El ID de widget es obligatorio para canales web.');
        return;
      }
    }

    setError(null);
    setIsSaving(true);

    try {
      const config = buildConfig();

      if (isEditing && channel) {
        const payload: ChannelUpdate = {
          type: form.type,
          name: form.name.trim(),
          external_id: form.external_id.trim(),
          config,
          is_active: form.is_active,
        };
        await updateChannel(channel.id, payload);
        onSaved('Canal actualizado correctamente.');
      } else {
        const payload: ChannelCreate = {
          tenant_id: form.tenant_id,
          type: form.type,
          name: form.name.trim(),
          external_id: form.external_id.trim(),
          config,
          is_active: form.is_active,
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
        if (!isSaving) {
          onClose();
        }
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
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="space-y-1.5">
          <label htmlFor="channel-tenant" className="block text-sm font-medium text-slate-700">
            Negocio
          </label>
          <select
            id="channel-tenant"
            value={form.tenant_id}
            onChange={(event) => setForm((prev) => ({ ...prev, tenant_id: event.target.value }))}
            disabled={isSaving || isEditing || isLoadingTenants}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
            required
          >
            <option value="">
              {isLoadingTenants ? 'Cargando negocios...' : 'Selecciona un negocio'}
            </option>
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id}>
                {tenant.name}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="Nombre del canal"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
          placeholder="WhatsApp Business"
          required
          disabled={isSaving}
        />

        <div className="space-y-1.5">
          <label htmlFor="channel-type" className="block text-sm font-medium text-slate-700">
            Tipo de canal
          </label>
          <select
            id="channel-type"
            value={form.type}
            onChange={(event) => setForm((prev) => ({ ...prev, type: event.target.value }))}
            disabled={isSaving || isEditing}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
          >
            {CHANNEL_TYPES.map((type) => (
              <option key={type} value={type}>
                {type.charAt(0).toUpperCase() + type.slice(1)}
              </option>
            ))}
          </select>
        </div>

        <Input
          label="ID externo"
          value={form.external_id}
          onChange={(event) => setForm((prev) => ({ ...prev, external_id: event.target.value }))}
          placeholder="wh_123456789"
          required
          disabled={isSaving}
        />

        {form.type === 'whatsapp' && (
          <>
            <Input
              label="Proveedor"
              value={form.provider || ''}
              onChange={(event) => setForm((prev) => ({ ...prev, provider: event.target.value }))}
              placeholder="twilio, waba, etc."
              required
              disabled={isSaving}
            />

            <Input
              label="ID de instancia"
              value={form.instance_id || ''}
              onChange={(event) => setForm((prev) => ({ ...prev, instance_id: event.target.value }))}
              placeholder="123456789"
              required
              disabled={isSaving}
            />

            <Input
              label="URL de webhook"
              value={form.webhook_url || ''}
              onChange={(event) => setForm((prev) => ({ ...prev, webhook_url: event.target.value }))}
              placeholder="https://example.com/webhook"
              required
              disabled={isSaving}
            />
          </>
        )}

        {form.type === 'web' && (
          <Input
            label="ID de widget"
            value={form.widget_id || ''}
            onChange={(event) => setForm((prev) => ({ ...prev, widget_id: event.target.value }))}
            placeholder="widget_12345"
            required
            disabled={isSaving}
          />
        )}

        <Checkbox
          label="Activo"
          checked={form.is_active}
          onChange={(e) =>
            setForm((prev) => ({
              ...prev,
              is_active: e.target.checked,
            }))
          }
          disabled={isSaving}
        />
      </form>
    </Modal>
  );
}
