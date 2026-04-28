'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import Checkbox from '@/components/ui/Checkbox';
import { getApiErrorMessage } from '@/services/api';
import { getPermissions } from '@/services/permissions';
import type { Permission } from '@/types/access';

interface PermissionSelectorProps {
  value: string[];
  onChange: (permissionIds: string[]) => void;
  disabled?: boolean;
}

const PERMISSION_GROUPS = ['users', 'roles', 'conversations', 'contacts', 'bot_config', 'channels', 'metrics', 'audit'] as const;
type PermissionGroup = (typeof PERMISSION_GROUPS)[number] | 'other';

const PERMISSION_GROUP_LABELS: Record<PermissionGroup, string> = {
  users: 'Usuarios',
  roles: 'Roles',
  conversations: 'Conversaciones',
  contacts: 'Contactos',
  bot_config: 'Configuración del bot',
  channels: 'Canales',
  metrics: 'Métricas',
  audit: 'Auditoría',
  other: 'Otros',
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

function toUniqueIds(ids: string[]): string[] {
  return Array.from(new Set(ids));
}

function haveSameMembers(a: string[], b: string[]): boolean {
  if (a.length !== b.length) {
    return false;
  }

  const bSet = new Set(b);
  return a.every((id) => bSet.has(id));
}

export default function PermissionSelector({ value, onChange, disabled = false }: PermissionSelectorProps) {
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previousNonSystemAdminPermissions, setPreviousNonSystemAdminPermissions] = useState<string[]>([]);

  const loadPermissions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const permissionList = await getPermissions();
      setAllPermissions(permissionList);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No se pudieron cargar los permisos.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPermissions();
  }, [loadPermissions]);

  const allPermissionIds = useMemo(() => allPermissions.map((permission) => permission.id), [allPermissions]);

  const systemAdminPermission = useMemo(
    () => allPermissions.find((permission) => isSystemAdminPermission(permission)) ?? null,
    [allPermissions],
  );

  const normalizedValue = useMemo(() => toUniqueIds(value), [value]);

  const isSystemAdminSelected = Boolean(
    systemAdminPermission && normalizedValue.includes(systemAdminPermission.id),
  );

  const groupedPermissions = useMemo(() => {
    const groupOrder: PermissionGroup[] = [...PERMISSION_GROUPS, 'other'];
    const grouped = new Map<PermissionGroup, Permission[]>(groupOrder.map((group) => [group, [] as Permission[]]));

    allPermissions.forEach((permission) => {
      if (isSystemAdminPermission(permission)) {
        return;
      }

      const group = getPermissionGroup(permission.code);
      grouped.get(group)?.push(permission);
    });

    return groupOrder
      .map((group) => ({
        key: group,
        label: PERMISSION_GROUP_LABELS[group],
        permissions: (grouped.get(group) ?? []).sort((a, b) => a.code.localeCompare(b.code)),
      }))
      .filter((group) => group.permissions.length > 0);
  }, [allPermissions]);

  useEffect(() => {
    if (allPermissionIds.length === 0) {
      return;
    }

    const validIds = normalizedValue.filter((permissionId) => allPermissionIds.includes(permissionId));
    if (!haveSameMembers(validIds, normalizedValue)) {
      onChange(validIds);
    }
  }, [allPermissionIds, normalizedValue, onChange]);

  useEffect(() => {
    if (!isSystemAdminSelected || !systemAdminPermission) {
      return;
    }

    const syncedValue = toUniqueIds([systemAdminPermission.id, ...allPermissionIds]);
    if (!haveSameMembers(syncedValue, normalizedValue)) {
      onChange(syncedValue);
    }
  }, [allPermissionIds, isSystemAdminSelected, normalizedValue, onChange, systemAdminPermission]);

  useEffect(() => {
    if (!systemAdminPermission || isSystemAdminSelected) {
      return;
    }

    setPreviousNonSystemAdminPermissions(
      normalizedValue.filter((permissionId) => permissionId !== systemAdminPermission.id),
    );
  }, [isSystemAdminSelected, normalizedValue, systemAdminPermission]);

  const togglePermission = (permissionId: string) => {
    if (disabled) {
      return;
    }

    if (isSystemAdminSelected && permissionId !== systemAdminPermission?.id) {
      return;
    }

    const updated = normalizedValue.includes(permissionId)
      ? normalizedValue.filter((id) => id !== permissionId)
      : [...normalizedValue, permissionId];

    onChange(updated);
  };

  const toggleSystemAdmin = (checked: boolean) => {
    if (disabled || !systemAdminPermission) {
      return;
    }

    if (checked) {
      setPreviousNonSystemAdminPermissions(normalizedValue.filter((id) => id !== systemAdminPermission.id));
      onChange(toUniqueIds([systemAdminPermission.id, ...allPermissionIds]));
      return;
    }

    const restored = previousNonSystemAdminPermissions.filter(
      (permissionId) => permissionId !== systemAdminPermission.id && allPermissionIds.includes(permissionId),
    );
    onChange(restored);
  };

  const togglePermissionGroup = (permissionIds: string[], checked: boolean) => {
    if (disabled || isSystemAdminSelected) {
      return;
    }

    if (checked) {
      onChange(toUniqueIds([...normalizedValue, ...permissionIds]));
      return;
    }

    const groupPermissionIdSet = new Set(permissionIds);
    onChange(normalizedValue.filter((permissionId) => !groupPermissionIdSet.has(permissionId)));
  };

  if (isLoading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-8 text-center text-sm text-slate-500">
        Cargando permisos...
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-3">
        <p className="text-sm text-rose-700">{error}</p>
        <Button type="button" variant="secondary" onClick={() => void loadPermissions()} disabled={disabled}>
          Reintentar
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {systemAdminPermission ? (
        <Checkbox
          label="Administrador del sistema"
          description={`Acceso completo del tenant actual (${systemAdminPermission.code})`}
          checked={isSystemAdminSelected}
          onChange={(event) => toggleSystemAdmin(event.target.checked)}
          disabled={disabled}
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
            const isGroupChecked =
              groupPermissionIds.length > 0 &&
              groupPermissionIds.every((permissionId) => normalizedValue.includes(permissionId));

            return (
              <div key={group.key} className="rounded-lg border border-slate-200 bg-slate-50/70 p-3">
                <div className="mb-3">
                  <Checkbox
                    label={group.label}
                    description={`Seleccionar los ${group.permissions.length} permisos`}
                    checked={isGroupChecked}
                    onChange={(event) => togglePermissionGroup(groupPermissionIds, event.target.checked)}
                    disabled={disabled}
                  />
                </div>

                <div className="grid grid-cols-1 gap-3 pl-2 md:grid-cols-2">
                  {group.permissions.map((permission) => (
                    <Checkbox
                      key={permission.id}
                      label={permission.name}
                      description={permission.code}
                      checked={normalizedValue.includes(permission.id)}
                      onChange={() => togglePermission(permission.id)}
                      disabled={disabled}
                    />
                  ))}
                </div>
              </div>
            );
          })}

          {groupedPermissions.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-500">
              No hay permisos agrupados disponibles.
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

