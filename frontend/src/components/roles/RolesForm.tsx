'use client';

import { useEffect, useMemo, useState } from 'react';
import PermissionSelector from '@/components/permissions/PermissionSelector';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import Textarea from '@/components/ui/Textarea';
import FormSection from '@/components/ui/FormSection';
import { getApiErrorMessage } from '@/services/api';
import { createRole, updateRole } from '@/services/roles';
import type { Role } from '@/types/access';

interface RolesFormProps {
  open: boolean;
  onClose: () => void;
  role?: Role | null;
  onSuccess: (message: string) => void;
}

interface FormState {
  name: string;
  description: string;
  permissions: string[];
}

const initialForm: FormState = {
  name: '',
  description: '',
  permissions: [],
};

function normalizeIds(ids: string[]): string[] {
  return Array.from(new Set(ids));
}

export default function RolesForm({ open, onClose, role, onSuccess }: RolesFormProps) {
  const isEditing = Boolean(role);

  const [form, setForm] = useState<FormState>(initialForm);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    setForm({
      name: role?.name ?? '',
      description: role?.description ?? '',
      permissions: normalizeIds((role?.permissions ?? []).map((permission) => permission.id)),
    });
    setError(null);
  }, [open, role]);

  const canSubmit = useMemo(
    () => form.name.trim().length > 0 && form.permissions.length > 0 && !isSaving,
    [form.name, form.permissions.length, isSaving],
  );

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const trimmedName = form.name.trim();
    if (!trimmedName) {
      setError('El nombre es obligatorio.');
      return;
    }

    const uniquePermissions = normalizeIds(form.permissions);
    if (uniquePermissions.length === 0) {
      setError('Selecciona al menos un permiso.');
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const payload = {
        name: trimmedName,
        description: form.description.trim() || null,
        permissions: uniquePermissions,
      };

      if (isEditing && role) {
        await updateRole(role.id, payload);
        onSuccess('Rol actualizado correctamente.');
      } else {
        await createRole(payload);
        onSuccess('Rol creado correctamente.');
      }

      onClose();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No se pudo guardar el rol.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={open}
      title={isEditing ? 'Editar rol' : 'Crear rol'}
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
          <Button type="submit" form="role-form" disabled={!canSubmit}>
            {isSaving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear rol'}
          </Button>
        </div>
      }
    >
      <form id="role-form" className="space-y-5" onSubmit={submit}>
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
        ) : null}

        <Input
          label="Nombre"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
          placeholder="Supervisor"
          required
          disabled={isSaving}
        />

        <Textarea
          id="role-description"
          label="Descripcion"
          value={form.description}
          onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
          placeholder="Describe lo que este rol puede hacer"
          rows={3}
          disabled={isSaving}
        />

        <FormSection title="Permisos" description="Define permisos por categoria funcional.">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm text-slate-600">Seleccionados</span>
            <Badge label={`${form.permissions.length}`} tone="info" />
          </div>
          <PermissionSelector
            value={form.permissions}
            onChange={(permissionIds) => setForm((prev) => ({ ...prev, permissions: normalizeIds(permissionIds) }))}
            disabled={isSaving}
          />
        </FormSection>
      </form>
    </Modal>
  );
}
