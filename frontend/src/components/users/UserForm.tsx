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

interface UserFormProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
  onSaved: (message: string) => void;
}

interface FormState {
  name: string;
  email: string;
  password: string;
  roleId: string;
  isActive: boolean;
  isBackdoor: boolean;
}

const PERMISSION_GROUPS = ['users', 'roles', 'conversations', 'contacts', 'bot_config', 'channels', 'metrics', 'audit'] as const;
type PermissionGroup = (typeof PERMISSION_GROUPS)[number] | 'other';

const PERMISSION_GROUP_LABELS: Record<PermissionGroup, string> = {
  users: 'Users',
  roles: 'Roles',
  conversations: 'Conversations',
  contacts: 'Contacts',
  bot_config: 'Bot Config',
  channels: 'Channels',
  metrics: 'Metrics',
  audit: 'Audit',
  other: 'Other',
};

const initialForm: FormState = {
  name: '',
  email: '',
  password: '',
  roleId: '',
  isActive: true,
  isBackdoor: false,
};

function normalizePermissionCode(code: string): string {
  return code.trim().toLowerCase();
}

function isSystemAdminPermission(permission: Permission): boolean {
  const code = normalizePermissionCode(permission.code);
  return code === 'system.admin' || code === 'system_admin';
}

function getPermissionGroup(permissionCode: string): PermissionGroup {
  const normalized = normalizePermissionCode(permissionCode);

  for (const group of PERMISSION_GROUPS) {
    if (normalized.startsWith(`${group}.`) || normalized.startsWith(`${group}_`)) {
      return group;
    }
  }

  return 'other';
}

export default function UserForm({ isOpen, user, onClose, onSaved }: UserFormProps) {
  const isEditing = Boolean(user);
  const [form, setForm] = useState<FormState>(initialForm);
  const [selectedPermissions, setSelectedPermissions] = useState<string[]>([]);
  const [previousNonSuperadminPermissions, setPreviousNonSuperadminPermissions] = useState<string[]>([]);
  const [previousBackdoorPermissions, setPreviousBackdoorPermissions] = useState<string[]>([]);
  const [previousBackdoorRoleId, setPreviousBackdoorRoleId] = useState('');
  const [roles, setRoles] = useState<Role[]>([]);
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [isLoadingMeta, setIsLoadingMeta] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const initialRoleId = user?.role?.id ?? '';
    const initialPermissionIds = (user?.permissions ?? []).map((permission) => permission.id);
    const initialIsBackdoor = Boolean(user?.is_backdoor);

    setForm({
      name: user?.name ?? '',
      email: user?.email ?? '',
      password: '',
      roleId: initialIsBackdoor ? '' : initialRoleId,
      isActive: user?.is_active ?? true,
      isBackdoor: initialIsBackdoor,
    });
    setSelectedPermissions(initialIsBackdoor ? [] : initialPermissionIds);
    setPreviousNonSuperadminPermissions(initialPermissionIds);
    setPreviousBackdoorPermissions(initialPermissionIds);
    setPreviousBackdoorRoleId(initialRoleId);
    setError(null);

    const fetchMeta = async () => {
      try {
        setIsLoadingMeta(true);
        const [roleList, permissionList] = await Promise.all([getRoles(), getPermissions()]);
        setRoles(roleList);
        setAllPermissions(permissionList);
      } catch (requestError) {
        setError(getApiErrorMessage(requestError, 'Unable to load role and permission data.'));
      } finally {
        setIsLoadingMeta(false);
      }
    };

    void fetchMeta();
  }, [isOpen, user]);

  const selectedRole = useMemo(
    () => roles.find((role) => role.id === form.roleId) ?? null,
    [form.roleId, roles],
  );

  const rolePermissionIds = useMemo(
    () => new Set((selectedRole?.permissions ?? []).map((permission) => permission.id)),
    [selectedRole],
  );

  const visiblePermissions = useMemo(() => {
    if (!selectedRole) {
      return allPermissions;
    }

    const merged = new Map<string, Permission>();
    allPermissions.forEach((permission) => {
      merged.set(permission.id, permission);
    });
    selectedRole.permissions.forEach((permission) => {
      merged.set(permission.id, permission);
    });

    return Array.from(merged.values());
  }, [allPermissions, selectedRole]);

  const allPermissionIds = useMemo(() => allPermissions.map((permission) => permission.id), [allPermissions]);

  const systemAdminPermission = useMemo(
    () => allPermissions.find((permission) => isSystemAdminPermission(permission)) ?? null,
    [allPermissions],
  );

  const isSystemAdminSelected = Boolean(
    systemAdminPermission && selectedPermissions.includes(systemAdminPermission.id),
  );

  const groupedPermissions = useMemo(() => {
    const groupOrder: PermissionGroup[] = [...PERMISSION_GROUPS, 'other'];
    const grouped = new Map<PermissionGroup, Permission[]>(groupOrder.map((group) => [group, [] as Permission[]]));

    visiblePermissions.forEach((permission) => {
      if (isSystemAdminPermission(permission)) {
        return;
      }
      const group = getPermissionGroup(permission.code);
      grouped.get(group)?.push(permission);
    });

    return groupOrder.map((group) => ({
      key: group,
      label: PERMISSION_GROUP_LABELS[group],
      permissions: (grouped.get(group) ?? []).sort((a, b) => a.code.localeCompare(b.code)),
    })).filter((group) => group.permissions.length > 0);
  }, [visiblePermissions]);

  useEffect(() => {
    if (!isSystemAdminSelected || !systemAdminPermission) {
      return;
    }

    setSelectedPermissions(Array.from(new Set([systemAdminPermission.id, ...allPermissionIds])));
  }, [allPermissionIds, isSystemAdminSelected, systemAdminPermission]);

  useEffect(() => {
    if (!selectedRole) {
      return;
    }

    const inherited = selectedRole.permissions.map((permission) => permission.id);
    setSelectedPermissions((prev) => Array.from(new Set([...inherited, ...prev])));
  }, [selectedRole]);

  const togglePermission = (permissionId: string) => {
    if (isSystemAdminSelected && permissionId !== systemAdminPermission?.id) {
      return;
    }

    setSelectedPermissions((prev) => {
      if (prev.includes(permissionId)) {
        return prev.filter((id) => id !== permissionId);
      }
      return [...prev, permissionId];
    });
  };

  const toggleSystemAdmin = (checked: boolean) => {
    if (!systemAdminPermission) {
      return;
    }

    if (checked) {
      setPreviousNonSuperadminPermissions(selectedPermissions.filter((id) => id !== systemAdminPermission.id));
      setSelectedPermissions(Array.from(new Set([systemAdminPermission.id, ...allPermissionIds])));
      return;
    }

    setSelectedPermissions(
      previousNonSuperadminPermissions.filter(
        (permissionId) => permissionId !== systemAdminPermission.id && allPermissionIds.includes(permissionId),
      ),
    );
  };

  const togglePermissionGroup = (permissionIds: string[], checked: boolean) => {
    if (isSystemAdminSelected) {
      return;
    }

    setSelectedPermissions((prev) => {
      if (checked) {
        return Array.from(new Set([...prev, ...permissionIds]));
      }
      const groupPermissionIdSet = new Set(permissionIds);
      return prev.filter((id) => !groupPermissionIdSet.has(id));
    });
  };

  const toggleBackdoor = (checked: boolean) => {
    if (checked) {
      setPreviousBackdoorRoleId(form.roleId);
      setPreviousBackdoorPermissions(selectedPermissions);
      setForm((prev) => ({ ...prev, isBackdoor: true, roleId: '' }));
      setSelectedPermissions([]);
      return;
    }

    const restoredPermissions = previousBackdoorPermissions.filter((permissionId) => allPermissionIds.includes(permissionId));
    setForm((prev) => ({ ...prev, isBackdoor: false, roleId: previousBackdoorRoleId }));
    setSelectedPermissions(restoredPermissions);
    setPreviousNonSuperadminPermissions(
      restoredPermissions.filter((permissionId) => permissionId !== systemAdminPermission?.id),
    );
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!form.name.trim() || !form.email.trim()) {
      setError('Name and email are required.');
      return;
    }

    if (!isEditing && form.password.trim().length < 6) {
      setError('Password is required and must have at least 6 characters.');
      return;
    }

    setError(null);
    setIsSaving(true);

    try {
      const normalizedPermissions = Array.from(new Set(selectedPermissions));
      const permissionsToSend =
        isSystemAdminSelected && systemAdminPermission
          ? [systemAdminPermission.id]
          : form.roleId
            ? normalizedPermissions.filter((permissionId) => !rolePermissionIds.has(permissionId))
            : normalizedPermissions;

      if (isEditing && user) {
        const basePayload = {
          name: form.name.trim(),
          email: form.email.trim(),
          is_active: form.isActive,
          ...(form.password.trim() ? { password: form.password.trim() } : {}),
        };

        if (form.isBackdoor) {
          await updateUser(user.id, {
            ...basePayload,
            is_backdoor: true,
          });
        } else {
          await updateUser(user.id, {
            ...basePayload,
            is_backdoor: false,
            role_id: form.roleId || null,
            permissions: permissionsToSend,
          });
        }
        onSaved('User updated successfully.');
      } else {
        const basePayload = {
          name: form.name.trim(),
          email: form.email.trim(),
          password: form.password.trim(),
          is_active: form.isActive,
        };

        if (form.isBackdoor) {
          await createUser({
            ...basePayload,
            is_backdoor: true,
          });
        } else {
          await createUser({
            ...basePayload,
            is_backdoor: false,
            role_id: form.roleId || null,
            permissions: permissionsToSend,
          });
        }
        onSaved('User created successfully.');
      }

      onClose();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Unable to save user.'));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      title={isEditing ? 'Edit User' : 'Create User'}
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
          <Button type="submit" form="user-form" disabled={isLoadingMeta || isSaving}>
            {isSaving ? 'Saving...' : isEditing ? 'Save Changes' : 'Create User'}
          </Button>
        </div>
      }
    >
      <form id="user-form" className="space-y-5" onSubmit={submit}>
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
        ) : null}

        {isLoadingMeta ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-8 text-center text-sm text-slate-500">
            Loading roles and permissions...
          </div>
        ) : (
          <>
            <div className="space-y-3">
              <Checkbox
                label="Backdoor (superadmin global)"
                description="Acceso global total. Anula roles y permisos del tenant."
                checked={form.isBackdoor}
                onChange={(event) => toggleBackdoor(event.target.checked)}
              />

              <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                <p>
                  <strong>Backdoor:</strong> acceso global a todos los negocios.
                </p>
                <p>
                  <strong>Administrador del sistema:</strong> acceso solo al tenant actual.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Input
                label="Name"
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="Jane Doe"
                required
              />
              <Input
                label="Email"
                type="email"
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                placeholder="jane@multisoft.com"
                required
              />
            </div>

            {!isEditing ? (
              <Input
                label="Password"
                type="password"
                value={form.password}
                onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                placeholder="At least 6 characters"
                required
              />
            ) : (
              <Input
                label="Password (optional)"
                type="password"
                value={form.password}
                onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
                placeholder="Leave empty to keep current password"
              />
            )}

            {form.isBackdoor ? (
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                Este usuario tiene acceso total a todos los negocios
              </div>
            ) : (
              <>
                <div className="space-y-1.5">
                  <label htmlFor="role-select" className="block text-sm font-medium text-slate-700">
                    Role
                  </label>
                  <select
                    id="role-select"
                    value={form.roleId}
                    onChange={(event) => setForm((prev) => ({ ...prev, roleId: event.target.value }))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200"
                  >
                    <option value="">No role</option>
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>
                        {role.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-slate-800">Permissions</h3>
                    {selectedRole ? (
                      <span className="rounded-full bg-sky-50 px-2 py-1 text-xs font-medium text-sky-700">
                        Role selected: {selectedRole.name}
                      </span>
                    ) : null}
                  </div>

                  {selectedRole ? (
                    <p className="text-xs text-slate-500">
                      Role permissions are inherited by default. You can add or remove user overrides below.
                    </p>
                  ) : (
                    <p className="text-xs text-slate-500">
                      Select permissions by group or individually.
                    </p>
                  )}

                  {systemAdminPermission ? (
                    <Checkbox
                      label="Administrador del sistema"
                      description={`Acceso completo del tenant actual (${systemAdminPermission.code})`}
                      checked={isSystemAdminSelected}
                      onChange={(event) => toggleSystemAdmin(event.target.checked)}
                    />
                  ) : null}

                  {isSystemAdminSelected ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                      Administrador del sistema activo. Se habilitan todos los permisos del tenant.
                    </div>
                  ) : null}

                  {!isSystemAdminSelected ? (
                    <div className="space-y-3">
                      {groupedPermissions.map((group) => {
                        const groupPermissionIds = group.permissions.map((permission) => permission.id);
                        const isGroupChecked = groupPermissionIds.every((permissionId) =>
                          selectedPermissions.includes(permissionId),
                        );

                        return (
                          <div key={group.key} className="rounded-lg border border-slate-200 bg-slate-50/70 p-3">
                            <div className="mb-3">
                              <Checkbox
                                label={group.label}
                                description={`Select all ${group.permissions.length} permission(s)`}
                                checked={isGroupChecked}
                                onChange={(event) => togglePermissionGroup(groupPermissionIds, event.target.checked)}
                              />
                            </div>

                            <div className="grid grid-cols-1 gap-3 pl-2 md:grid-cols-2">
                              {group.permissions.map((permission) => (
                                <Checkbox
                                  key={permission.id}
                                  label={permission.name}
                                  description={permission.code}
                                  checked={selectedPermissions.includes(permission.id)}
                                  onChange={() => togglePermission(permission.id)}
                                />
                              ))}
                            </div>
                          </div>
                        );
                      })}

                      {groupedPermissions.length === 0 ? (
                        <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
                          No grouped permissions available.
                        </div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </>
            )}

            <Checkbox
              label="User is active"
              checked={form.isActive}
              onChange={(event) => setForm((prev) => ({ ...prev, isActive: event.target.checked }))}
            />
          </>
        )}
      </form>
    </Modal>
  );
}
