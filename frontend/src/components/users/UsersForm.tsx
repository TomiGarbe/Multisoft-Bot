'use client';

import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import Checkbox from '@/components/ui/Checkbox';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import { getApiErrorMessage } from '@/services/api';
import { getPermissions } from '@/services/permissions';
import { getRoles } from '@/services/roles';
import { createUser, updateUser } from '@/services/users';
import type { Permission, Role, User } from '@/types/access';

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
  isActive: boolean;
}

const initialForm: FormState = {
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  roleId: '',
  isActive: true,
};

const INTERNAL_ROLE_NAMES = ['super_admin', 'system_admin', 'tenant_owner', 'internal', 'backdoor', 'root'];

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

function roleUiLabel(role: Role): string {
  const normalized = normalizeText(role.name);
  if (normalized.includes('admin')) return 'Administrador';
  if (normalized.includes('supervisor')) return 'Supervisor';
  if (normalized.includes('operator') || normalized.includes('operador')) return 'Operador';
  return role.name;
}

export default function UsersForm({ isOpen, user, onClose, onSaved }: UsersFormProps) {
  const isEditing = Boolean(user);
  const [form, setForm] = useState<FormState>(initialForm);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [customizePermissions, setCustomizePermissions] = useState(false);
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
      isActive: user?.is_active ?? true,
    });
    setSelectedPermissions((user?.permissions ?? []).map((permission) => permission.id));
    setCustomizePermissions(false);
    setError(null);

    const fetchMeta = async () => {
      try {
        setIsLoadingMeta(true);
        const [roleList, permissionList] = await Promise.all([getRoles(), getPermissions()]);
        setRoles(roleList.filter((role) => !isInternalRole(role)));
        setAllPermissions(permissionList);
      } catch (requestError) {
        setError(getApiErrorMessage(requestError, 'No se pudieron cargar roles y permisos.'));
      } finally {
        setIsLoadingMeta(false);
      }
    };

    void fetchMeta();
  }, [isOpen, user]);

  const selectedRole = useMemo(() => roles.find((role) => role.id === form.roleId) ?? null, [form.roleId, roles]);

  const rolePermissionIds = useMemo(
    () => new Set((selectedRole?.permissions ?? []).map((permission) => permission.id)),
    [selectedRole],
  );

  const visiblePermissions = useMemo(() => {
    const merged = new Map<string, Permission>();
    allPermissions.forEach((permission) => merged.set(permission.id, permission));
    selectedRole?.permissions.forEach((permission) => merged.set(permission.id, permission));
    return Array.from(merged.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [allPermissions, selectedRole]);

  const togglePermission = (permissionId: string) => {
    setSelectedPermissions((prev) =>
      prev.includes(permissionId) ? prev.filter((id) => id !== permissionId) : [...prev, permissionId],
    );
  };

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
      const normalizedPermissions = Array.from(new Set(selectedPermissions));
      const permissionsToSend = !customizePermissions
        ? []
        : form.roleId
          ? normalizedPermissions.filter((permissionId) => !rolePermissionIds.has(permissionId))
          : normalizedPermissions;

      if (isEditing && user) {
        await updateUser(user.id, {
          name: fullName,
          email,
          is_active: form.isActive,
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
          is_active: form.isActive,
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

            <div className="space-y-1.5">
              <label htmlFor="role-select" className="block text-sm font-medium text-slate-700">
                Rol
              </label>
              <select
                id="role-select"
                value={form.roleId}
                onChange={(event) => setForm((prev) => ({ ...prev, roleId: event.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
              >
                <option value="">Sin rol</option>
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {roleUiLabel(role)}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3">
              <Checkbox
                label="Personalizar permisos"
                description="Opcional: agrega permisos puntuales sobre el rol seleccionado."
                checked={customizePermissions}
                onChange={(event) => setCustomizePermissions(event.target.checked)}
              />

              {customizePermissions ? (
                <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border border-slate-200 bg-white p-3">
                  {visiblePermissions.length === 0 ? (
                    <p className="text-xs text-slate-500">No hay permisos disponibles.</p>
                  ) : (
                    visiblePermissions.map((permission) => (
                      <Checkbox
                        key={permission.id}
                        label={permission.name}
                        description={permission.code}
                        checked={selectedPermissions.includes(permission.id)}
                        onChange={() => togglePermission(permission.id)}
                      />
                    ))
                  )}
                </div>
              ) : null}
            </div>

            <Checkbox
              label="Usuario activo"
              checked={form.isActive}
              onChange={(event) => setForm((prev) => ({ ...prev, isActive: event.target.checked }))}
            />
          </>
        )}
      </form>
    </Modal>
  );
}

