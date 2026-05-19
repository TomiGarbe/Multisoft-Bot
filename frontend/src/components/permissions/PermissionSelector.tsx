'use client';

import {
  BarChart3,
  Cable,
  KeyRound,
  LayoutDashboard,
  MessagesSquare,
  Search,
  ShieldCheck,
  Sliders,
  UserCog,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import Input from '@/components/ui/Input';
import PermissionToggle from '@/components/ui/PermissionToggle';
import Switch from '@/components/ui/Switch';
import { getApiErrorMessage } from '@/services/api';
import { getPermissions } from '@/services/permissions';
import type { Permission } from '@/types/access';

interface PermissionSelectorProps {
  value: string[];
  onChange: (permissionIds: string[]) => void;
  disabled?: boolean;
}

interface PermissionCategory {
  key: string;
  title: string;
  description?: string;
  icon: ReactNode;
}

const CATEGORIES: PermissionCategory[] = [
  {
    key: 'dashboard',
    title: 'Dashboard',
    description: 'Metricas, analiticas y vistas generales.',
    icon: <LayoutDashboard className="h-4 w-4" />,
  },
  {
    key: 'roles',
    title: 'Roles y permisos',
    description: 'Politicas de acceso y gestion de roles.',
    icon: <ShieldCheck className="h-4 w-4" />,
  },
  {
    key: 'users',
    title: 'Usuarios',
    description: 'Administracion de usuarios, roles y asignaciones granulares.',
    icon: <UserCog className="h-4 w-4" />,
  },
  {
    key: 'conversations',
    title: 'Conversaciones',
    description: 'Conversaciones, mensajes, multimedia y datos relacionados al chat.',
    icon: <MessagesSquare className="h-4 w-4" />,
  },
  {
    key: 'channels',
    title: 'Canales',
    description: 'Canales, reconexion, sincronizacion y configuraciones del canal.',
    icon: <BarChart3 className="h-4 w-4" />,
  },
  {
    key: 'integrations',
    title: 'Integraciones',
    description: 'Bot actions, webhooks y proveedores externos.',
    icon: <Cable className="h-4 w-4" />,
  },
  {
    key: 'settings',
    title: 'Configuracion',
    description: 'Configuracion general, API keys, automatizaciones y AI settings.',
    icon: <Sliders className="h-4 w-4" />,
  },
];

const CATEGORY_ACTION_ICONS: Record<string, ReactNode> = {
  read: <BarChart3 className="h-4 w-4" />,
  view: <BarChart3 className="h-4 w-4" />,
  list: <BarChart3 className="h-4 w-4" />,
  create: <Sliders className="h-4 w-4" />,
  update: <UserCog className="h-4 w-4" />,
  edit: <UserCog className="h-4 w-4" />,
  delete: <KeyRound className="h-4 w-4" />,
  manage: <ShieldCheck className="h-4 w-4" />,
};

function normalize(value: string): string {
  return value.trim().toLowerCase();
}

function humanizePermission(permission: Permission): string {
  const source = permission.name || permission.code;
  const sanitized = source.replace(/[._]/g, ' ').replace(/\s+/g, ' ').trim();
  return sanitized.charAt(0).toUpperCase() + sanitized.slice(1);
}

function resolvePermissionIcon(permission: Permission): ReactNode {
  const haystack = `${normalize(permission.code)} ${normalize(permission.name)}`;
  const found = Object.entries(CATEGORY_ACTION_ICONS).find(([key]) => haystack.includes(key));
  return found ? found[1] : <ShieldCheck className="h-4 w-4" />;
}

function unique(ids: string[]): string[] {
  return Array.from(new Set(ids));
}

function resolvePageKeys(permission: Permission): string[] {
  const explicit = (permission.pages ?? []).filter(Boolean);
  if (explicit.length > 0) return unique(explicit);

  const moduleKey = (permission.module ?? permission.code.split('.')[0] ?? '').toLowerCase();
  const fallbackByModule: Record<string, string[]> = {
    analytics: ['dashboard'],
    conversations: ['conversations'],
    messages: ['conversations'],
    contacts: ['conversations'],
    contact_notes: ['conversations'],
    contact_tags: ['conversations', 'settings'],
    contact_types: ['conversations', 'settings'],
    user_types: ['conversations', 'settings'],
    users: ['users'],
    roles: ['roles', 'users'],
    permissions: ['roles', 'users'],
    channels: ['channels', 'conversations'],
    channel_config: ['channels', 'settings', 'integrations'],
    bot_actions: ['integrations'],
    api_keys: ['settings'],
  };
  return fallbackByModule[moduleKey] ?? [];
}

export default function PermissionSelector({ value, onChange, disabled = false }: PermissionSelectorProps) {
  const [allPermissions, setAllPermissions] = useState<Permission[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  const loadPermissions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const permissionList = await getPermissions();
      setAllPermissions(permissionList.filter((permission) => permission.assignable !== false && permission.tenant_visible !== false));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'No se pudieron cargar los permisos.'));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPermissions();
  }, [loadPermissions]);

  const normalizedValue = useMemo(() => unique(value), [value]);
  const allowedIds = useMemo(() => new Set(allPermissions.map((permission) => permission.id)), [allPermissions]);

  useEffect(() => {
    const filtered = normalizedValue.filter((id) => allowedIds.has(id));
    if (filtered.length !== normalizedValue.length) {
      onChange(filtered);
    }
  }, [allowedIds, normalizedValue, onChange]);

  const categorizedPermissions = useMemo(() => {
    const grouped = new Map<string, Permission[]>();
    const q = search.trim().toLowerCase();

    CATEGORIES.forEach((category) => grouped.set(category.key, []));

    allPermissions.forEach((permission) => {
      const pageKeys = resolvePageKeys(permission);
      if (q) {
        const haystack = `${permission.code} ${permission.name}`.toLowerCase();
        if (!haystack.includes(q)) return;
      }
      pageKeys.forEach((pageKey) => {
        if (grouped.has(pageKey)) {
          grouped.get(pageKey)?.push(permission);
        }
      });
    });

    return CATEGORIES.map((category) => ({
      ...category,
      permissions: (grouped.get(category.key) ?? []).sort((a, b) =>
        humanizePermission(a).localeCompare(humanizePermission(b)),
      ),
    })).filter((category) => category.permissions.length > 0);
  }, [allPermissions, search]);

  const togglePermission = (permissionId: string) => {
    if (disabled) return;
    if (normalizedValue.includes(permissionId)) {
      onChange(normalizedValue.filter((id) => id !== permissionId));
      return;
    }
    onChange([...normalizedValue, permissionId]);
  };

  const toggleCategory = (categoryKey: string, permissions: Permission[], allSelected: boolean) => {
    if (disabled) return;
    const ids = permissions.map((permission) => permission.id);
    if (allSelected) {
      onChange(normalizedValue.filter((id) => !ids.includes(id)));
    } else {
      onChange(unique([...normalizedValue, ...ids]));
    }
    void categoryKey;
  };

  if (isLoading) {
    return <EmptyState title="Cargando permisos..." description="Obteniendo catalogo de permisos del negocio." />;
  }

  if (error) {
    return (
      <div className="space-y-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3">
        <p className="text-sm text-rose-700">{error}</p>
        <Button type="button" variant="secondary" onClick={() => void loadPermissions()} disabled={disabled}>
          Reintentar
        </Button>
      </div>
    );
  }

  if (allPermissions.length === 0) {
    return (
      <EmptyState
        title="No hay permisos visibles"
        description="No se encontraron permisos aptos para exponer en el frontend."
      />
    );
  }

  return (
    <div className="space-y-4">
      <Input
        id="permissions-search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Buscar permisos..."
        leadingIcon={<Search />}
      />

      {categorizedPermissions.length === 0 ? (
        <EmptyState
          title="Sin resultados"
          description="No hay permisos que coincidan con la busqueda."
          compact
        />
      ) : (
        categorizedPermissions.map((category) => {
          const selectedInCategory = category.permissions.filter((permission) =>
            normalizedValue.includes(permission.id),
          ).length;
          const allSelected = selectedInCategory === category.permissions.length;

          return (
            <section
              key={category.key}
              className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
            >
              <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 bg-slate-50/60 px-4 py-3">
                <div className="flex min-w-0 items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-sky-600 ring-1 ring-inset ring-slate-200">
                    {category.icon}
                  </span>
                  <div className="min-w-0">
                    <h4 className="text-sm font-semibold text-slate-900">{category.title}</h4>
                    {category.description ? (
                      <p className="text-xs text-slate-500">{category.description}</p>
                    ) : null}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Switch
                    layout="inline"
                    size="sm"
                    label="Seleccionar todos"
                    checked={allSelected}
                    disabled={disabled}
                    onChange={() => toggleCategory(category.key, category.permissions, allSelected)}
                  />
                  <Badge
                    tone={selectedInCategory > 0 ? 'info' : 'neutral'}
                    label={`${selectedInCategory}/${category.permissions.length} seleccionados`}
                    variant="soft"
                  />
                </div>
              </header>

              <div className="grid grid-cols-1 gap-2 p-3 md:grid-cols-2">
                {category.permissions.map((permission) => (
                  <PermissionToggle
                    key={permission.id}
                    label={humanizePermission(permission)}
                    description={permission.code}
                    checked={normalizedValue.includes(permission.id)}
                    onChange={() => togglePermission(permission.id)}
                    disabled={disabled}
                    icon={resolvePermissionIcon(permission)}
                  />
                ))}
              </div>
            </section>
          );
        })
      )}
    </div>
  );
}
