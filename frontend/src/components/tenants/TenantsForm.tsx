'use client';

import { useEffect, useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Select from '@/components/ui/Select';
import Switch from '@/components/ui/Switch';
import Textarea from '@/components/ui/Textarea';
import {
  createTenant,
  updateTenant,
} from '@/services/tenants';
import type { Tenant } from '@/types/tenant';
import { getApiErrorMessage } from '@/services/api';
import { generateSlug } from '@/utils/slug';
import {
  DEFAULT_TENANT_TIMEZONE,
  isAllowedTenantTimezone,
  TENANT_TIMEZONE_OPTIONS,
  resolveTenantTimezone,
} from '@/constants/timezones';

interface Props {
  isOpen: boolean;
  tenant: Tenant | null;
  onClose: () => void;
  onSaved: (msg: string) => void;
}

export default function TenantsForm({
  isOpen,
  tenant,
  onClose,
  onSaved,
}: Props) {
  const isEditing = Boolean(tenant);
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [industry, setIndustry] = useState('');
  const [timezone, setTimezone] = useState(DEFAULT_TENANT_TIMEZONE);
  const [isActivo, setIsActivo] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isSaving, setIsSaving] = useState(false);
  const [slugTouched, setSlugTouched] = useState(false);

  useEffect(() => {
    if (tenant) {
      setName(tenant.name);
      setSlug(tenant.slug);
      setDescription(tenant.description ?? '');
      setIndustry(tenant.industry ?? '');
      setTimezone(resolveTenantTimezone(tenant.timezone));
      setIsActivo(tenant.is_active);
      setSlugTouched(true);
    } else {
      setName('');
      setSlug('');
      setDescription('');
      setIndustry('');
      setTimezone(DEFAULT_TENANT_TIMEZONE);
      setIsActivo(true);
      setSlugTouched(false);
    }
    setError(null);
  }, [tenant, isOpen]);

  useEffect(() => {
    if (!slugTouched) {
      setSlug(generateSlug(name));
    }
  }, [name, slugTouched]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!timezone) {
      setError('La zona horaria es obligatoria.');
      return;
    }
    if (!isAllowedTenantTimezone(timezone)) {
      setError('Selecciona una zona horaria valida de la lista.');
      return;
    }
    if (!name.trim()) {
      setError('El nombre es obligatorio.');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);

      const payload = {
        name: name.trim(),
        slug: slug.trim(),
        description: description.trim(),
        industry: industry.trim(),
        timezone,
        ...(tenant && { is_active: isActivo }),
      };

      if (tenant) {
        await updateTenant(tenant.id, payload);
        onSaved('Negocio actualizado correctamente.');
      } else {
        await createTenant(payload);
        onSaved('Negocio creado correctamente.');
      }

      onClose();
    } catch (err) {
      setError(getApiErrorMessage(err, 'Error al guardar el negocio'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={() => {
        if (!isSaving) onClose();
      }}
      title={isEditing ? 'Editar negocio' : 'Crear negocio'}
      description="Configura los datos basicos del tenant."
      footer={
        <div className="flex items-center justify-end gap-3">
          <Button variant="secondary" type="button" onClick={onClose} disabled={isSaving}>
            Cancelar
          </Button>
          <Button type="submit" form="tenant-form" loading={isSaving}>
            {isEditing ? 'Guardar cambios' : 'Crear negocio'}
          </Button>
        </div>
      }
    >
      <form id="tenant-form" className="space-y-5" onSubmit={handleSubmit}>
        {error ? (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Nombre"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Acme S.A."
            required
          />
          <Input
            label="Slug"
            value={slug}
            onChange={(e) => {
              setSlug(generateSlug(e.target.value));
              setSlugTouched(true);
            }}
            placeholder="acme"
            hint="Identificador unico para URLs"
          />
        </div>

        <Textarea
          label="Descripcion"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Que hace este negocio"
          rows={3}
        />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Industria"
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            placeholder="Retail, salud, fintech..."
          />
          <Select
            label="Zona horaria"
            id="tenant-timezone"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            options={TENANT_TIMEZONE_OPTIONS.map((option) => ({
              value: option.value,
              label: option.label,
            }))}
            required
          />
        </div>

        {tenant ? (
          <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3">
            <Switch
              label="Negocio activo"
              description="Si esta inactivo, los usuarios no pueden usarlo."
              checked={isActivo}
              onChange={(e) => setIsActivo(e.target.checked)}
            />
          </div>
        ) : null}
      </form>
    </Modal>
  );
}
