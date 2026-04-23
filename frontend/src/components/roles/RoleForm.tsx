'use client';

import { useEffect, useMemo, useState } from 'react';
import PermissionSelector from '@/components/permissions/PermissionSelector';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { getApiErrorMessage } from '@/services/api';
import { createRole, updateRole } from '@/services/roles';
import type { Role } from '@/types/access';

interface RoleFormProps {
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

export default function RoleForm({ open, onClose, role, onSuccess }: RoleFormProps) {
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
      setError('Name is required.');
      return;
    }

    const uniquePermissions = normalizeIds(form.permissions);
    if (uniquePermissions.length === 0) {
      setError('Select at least one permission.');
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
        onSuccess('Role updated successfully.');
      } else {
        await createRole(payload);
        onSuccess('Role created successfully.');
      }

      onClose();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to save role.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={open}
      title={isEditing ? 'Edit Role' : 'Create Role'}
      onClose={() => {
        if (!isSaving) {
          onClose();
        }
      }}
      footer={
        <div className="flex items-center justify-end gap-3">
          <Button variant="secondary" type="button" onClick={onClose} disabled={isSaving}>
            Cancel
          </Button>
          <Button type="submit" form="role-form" disabled={!canSubmit}>
            {isSaving ? 'Saving...' : isEditing ? 'Save Changes' : 'Create Role'}
          </Button>
        </div>
      }
    >
      <form id="role-form" className="space-y-5" onSubmit={submit}>
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
        ) : null}

        <Input
          label="Name"
          value={form.name}
          onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
          placeholder="Manager"
          required
          disabled={isSaving}
        />

        <div className="space-y-1.5">
          <label htmlFor="role-description" className="block text-sm font-medium text-slate-700">
            Description
          </label>
          <textarea
            id="role-description"
            value={form.description}
            onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
            placeholder="Describe what this role can do"
            rows={3}
            disabled={isSaving}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Permissions</h3>
            <span className="rounded-full bg-sky-50 px-2 py-1 text-xs font-medium text-sky-700">
              {form.permissions.length} selected
            </span>
          </div>

          <p className="text-xs text-slate-500">Select permissions by group or individually.</p>

          <PermissionSelector
            value={form.permissions}
            onChange={(permissionIds) => setForm((prev) => ({ ...prev, permissions: normalizeIds(permissionIds) }))}
            disabled={isSaving}
          />
        </div>
      </form>
    </Modal>
  );
}
