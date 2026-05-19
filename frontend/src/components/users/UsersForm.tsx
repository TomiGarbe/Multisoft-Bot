'use client';

import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import FormSection from '@/components/ui/FormSection';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PermissionSelector from '@/components/permissions/PermissionSelector';
import Select from '@/components/ui/Select';
import { getApiErrorMessage } from '@/services/api';
import { getRoles } from '@/services/roles';
import { createUser, updateUser } from '@/services/users';
import type { Role, User } from '@/types/access';

interface UsersFormProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
  onSaved: (message: string) => void;
}

interface FormState {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
  roleId: string;
}

const initialForm: FormState = {
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  roleId: '',
};

const INTERNAL_ROLE_NAMES = ['super_admin', 'system_admin', 'tenant_owner', 'internal', 'backdoor', 'root', 'administrador', 'admin'];

function normalizeText(value: string): string {
  return value.trim().toLowerCase().replace(/\s+/g, '_');
}

function isInternalRole(role: Role): boolean {
  const normalized = normalizeText(role.name);
  return INTERNAL_ROLE_NAMES.some((term) => normalized.includes(term));
}

function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function isStrongPassword(value: string): boolean {
  return value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /\d/.test(value);
}

function unique(values: string[]): string[] {
  return Array.from(new Set(values));
}

export default function UsersForm({ isOpen, user, onClose, onSaved }: UsersFormProps) {
  const isEditing = Boolean(user);
  const [form, setForm] = useState<FormState>(initialForm);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    const fullName = (user?.name ?? '').trim();
    const [firstName = '', ...lastParts] = fullName.split(' ').filter(Boolean);

    setForm({
      firstName,
      lastName: lastParts.join(' '),
      email: user?.email ?? '',
      password: '',
      confirmPassword: '',
      roleId: user?.role?.id ?? '',
    });
    setSelectedPermissions((user?.permissions ?? []).map((permission) => permission.id));
    setError(null);

    const fetchMeta = async () => {
      try {
        setIsLoadingMeta(true);
        const roleList = await getRoles();
        setRoles(roleList.filter((role) => !isInternalRole(role)));
      } catch (requestError) {
        setError(getApiErrorMessage(requestError, 'No se pudieron cargar roles y permisos.'));
      } finally {
        setIsLoadingMeta(false);
      }
    };

    void fetchMeta();
  }, [isOpen, user]);

  const selectedRole = useMemo(() => roles.find((role) => role.id === form.roleId) ?? null, [form.roleId, roles]);

  useEffect(() => {
    if (!isOpen) return;
    if (!selectedRole) return;
    setSelectedPermissions((prev) => unique([...selectedRole.permissions.map((permission) => permission.id), ...prev]));
  }, [isOpen, selectedRole?.id]);

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const firstName = form.firstName.trim();
    const lastName = form.lastName.trim();
    const fullName = `${firstName} ${lastName}`.trim();
    const email = form.email.trim();
    const password = form.password.trim();

    if (!firstName) {
      setError('El nombre es obligatorio.');
      return;
    }

    if (!isValidEmail(email)) {
      setError('Ingresa un email valido.');
      return;
    }

    if (!isEditing || password.length > 0) {
      if (!isStrongPassword(password)) {
        setError('La contrasena debe tener al menos 8 caracteres, mayuscula, minuscula y numero.');
        return;
      }
      if (password !== form.confirmPassword.trim()) {
        setError('La confirmacion de contrasena no coincide.');
        return;
      }
    }

    setError(null);
    setIsSaving(true);

    try {
      const permissionsToSend = unique(selectedPermissions);

      if (isEditing && user) {
        await updateUser(user.id, {
          name: fullName,
          email,
          role_id: form.roleId || null,
          permissions: permissionsToSend,
          ...(password ? { password } : {}),
          is_backdoor: false,
        });
        onSaved('Usuario actualizado correctamente.');
      } else {
        await createUser({
          name: fullName,
          email,
          password,
          role_id: form.roleId || null,
          permissions: permissionsToSend,
          is_backdoor: false,
          user_type: 'User',
        });
        onSaved('Usuario creado correctamente.');
      }

      onClose();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No se pudo guardar el usuario.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      title={isEditing ? 'Editar usuario' : 'Crear usuario'}
      onClose={() => {
        if (!isSaving) onClose();
      }}
      footer={
        <div className="flex items-center justify-end gap-3">
          <Button variant="secondary" type="button" onClick={onClose} disabled={isSaving}>
            Cancelar
          </Button>
          <Button type="submit" form="user-form" disabled={isLoadingMeta || isSaving}>
            {isSaving ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear usuario'}
          </Button>
        </div>
      }
    >
      <form id="user-form" className="space-y-5" onSubmit={submit}>
        {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div> : null}

        {isLoadingMeta ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-8 text-center text-sm text-slate-500">
            Cargando configuracion de usuario...
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Input
                label="Nombre"
                value={form.firstName}
                onChange={(event) => setForm((prev) => ({ ...prev, firstName: event.target.value }))}
                placeholder="Jane"
                required
              />
              <Input
                label="Apellido"
                value={form.lastName}
                onChange={(event) => setForm((prev) => ({ ...prev, lastName: event.target.value }))}
                placeholder="Doe"
              />
            </div>

            <Input
              label="Email"
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              placeholder="jane@empresa.com"
              required
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Input
                label={isEditing ? 'Nueva contrasena (opcional)' : 'Contrasena'}
                type="password"
                value={form.password}
                onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                placeholder="Minimo 8 caracteres"
                required={!isEditing}
              />
              <Input
                label={isEditing ? 'Confirmar nueva contrasena' : 'Confirmar contrasena'}
                type="password"
                value={form.confirmPassword}
                onChange={(event) => setForm((prev) => ({ ...prev, confirmPassword: event.target.value }))}
                placeholder="Repite la contrasena"
                required={!isEditing || Boolean(form.password.trim())}
              />
            </div>

            <Select
              label="Rol"
              id="role-select"
              value={form.roleId}
              onChange={(event) => setForm((prev) => ({ ...prev, roleId: event.target.value }))}
              options={roles.map((role) => ({ value: role.id, label: role.name }))}
              placeholder="Sin rol"
            />

            <FormSection
              title="Permisos"
              description={selectedRole ? `Permisos base heredados del rol: ${selectedRole.name}. Puedes sobrescribir por usuario.` : 'Selecciona permisos manuales para el usuario.'}
            >
              <PermissionSelector
                value={selectedPermissions}
                onChange={setSelectedPermissions}
                disabled={isSaving}
              />
            </FormSection>
          </>
        )}
      </form>
    </Modal>
  );
}
