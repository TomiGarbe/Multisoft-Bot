'use client';

import { useEffect, useState } from 'react';
import Button from '@/components/ui/Button';
import Modal from '@/components/ui/Modal';
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
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [description, setDescription] = useState('');
  const [industry, setIndustry] = useState('');
  const [timezone, setTimezone] = useState(DEFAULT_TENANT_TIMEZONE);
  const [isActivo, setIsActivo] = useState(true);

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
  }, [tenant]);

  // 🔥 Auto slug
  useEffect(() => {
    if (!slugTouched) {
      setSlug(generateSlug(name));
    }
  }, [name, slugTouched]);

  const handleSubmit = async () => {
    if (!timezone) {
      alert('La zona horaria es obligatoria.');
      return;
    }
    if (!isAllowedTenantTimezone(timezone)) {
      alert('Selecciona una zona horaria valida de la lista.');
      return;
    }

    try {
      setIsSaving(true);

      const payload = {
        name,
        slug,
        description,
        industry,
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
      alert(getApiErrorMessage(err, 'Error al guardar el negocio'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Negocio">
      <div className="space-y-4">

        {/* NAME */}
        <input
          className="w-full border p-2 rounded"
          placeholder="Nombre"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {/* SLUG */}
        <input
          className="w-full border p-2 rounded"
          placeholder="Slug"
          value={slug}
          onChange={(e) => {
            setSlug(generateSlug(e.target.value));
            setSlugTouched(true);
          }}
        />

        {/* DESCRIPTION */}
        <textarea
          className="w-full border p-2 rounded"
          placeholder="Descripcion"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />

        {/* INDUSTRY */}
        <input
          className="w-full border p-2 rounded"
          placeholder="Industria"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
        />

        {/* TIMEZONE */}
        <div className="space-y-1">
          <label htmlFor="tenant-timezone" className="block text-sm font-medium text-slate-700">
            Zona horaria
          </label>
          <select
            id="tenant-timezone"
            className="w-full rounded border border-slate-300 bg-white p-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            required
          >
            {TENANT_TIMEZONE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* ACTIVE */}
        {tenant && (
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isActivo}
              onChange={(e) => setIsActivo(e.target.checked)}
            />
            Activo
          </label>
        )}

        <div className="flex justify-end gap-2">
          <Button onClick={onClose} variant="secondary">
            Cancelar
          </Button>

          <Button onClick={handleSubmit} disabled={isSaving}>
            {isSaving ? 'Guardando...' : 'Guardar'}
          </Button>
        </div>
      </div>
    </Modal>
  );
}

