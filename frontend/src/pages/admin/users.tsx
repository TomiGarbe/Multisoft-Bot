import { Building2, KeyRound, Lock, Pencil, Plus, ShieldCheck, Trash2, UserCog, Users } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import EmptyState from '@/components/ui/EmptyState';
import IconButton from '@/components/ui/IconButton';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import PermissionToggle from '@/components/ui/PermissionToggle';
import Radio from '@/components/ui/Radio';
import Switch from '@/components/ui/Switch';
import Table from '@/components/ui/Table';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { useTenantContext } from '@/context/tenant-context';
import { useAuthToken } from '@/hooks/useAuthToken';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { createAdminUser, createBackdoorUser, deleteGlobalUser, getGlobalUsers, updateGlobalUser } from '@/services/users';
import type { User } from '@/types/access';
import type { Tenant } from '@/types/tenant';

type GlobalUserType = 'Administrador' | 'Backdoor';

function initialsOf(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('');
}

function isStrongPassword(value: string): boolean {
  return value.length >= 8 && /[A-Z]/.test(value) && /[a-z]/.test(value) && /\d/.test(value);
}

export default function GlobalUsersPage() {
  const toast = useToast();
  const { user: currentUser, tenants } = useTenantContext();
  const { authResolved, hasToken } = useAuthToken();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [type, setType] = useState<GlobalUserType>('Administrador');
  const [businessIds, setBusinessIds] = useState<string[]>([]);
  const [isActive, setIsActive] = useState(true);

  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const globalUsers = await getGlobalUsers();
      setUsers(globalUsers);
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los usuarios globales.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hasToken) void fetchAll();
  }, [hasToken]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handler = () => {
      if (hasToken) void fetchAll();
    };
    window.addEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
    return () => window.removeEventListener(TENANT_CONTEXT_CHANGED_EVENT, handler);
  }, [hasToken]);

  const admins = useMemo(() => users.filter((u) => u.user_type === 'Administrador'), [users]);
  const backdoors = useMemo(() => users.filter((u) => u.user_type === 'Backdoor'), [users]);

  const tenantsById = useMemo(() => {
    const map = new Map<string, Tenant>();
    tenants.forEach((tenant) => map.set(tenant.id, tenant));
    return map;
  }, [tenants]);

  const toggleBusiness = (businessId: string) => {
    setBusinessIds((prev) =>
      prev.includes(businessId) ? prev.filter((id) => id !== businessId) : [...prev, businessId],
    );
  };

  const resetForm = () => {
    setName('');
    setEmail('');
    setPassword('');
    setBusinessIds([]);
    setType('Administrador');
    setIsActive(true);
    setEditingUser(null);
    setFormError(null);
  };

  const openCreate = () => {
    resetForm();
    setIsOpen(true);
  };

  const openEdit = (user: User) => {
    setEditingUser(user);
    setName(user.name);
    setEmail(user.email);
    setPassword('');
    setType((user.user_type as GlobalUserType) ?? 'Administrador');
    setBusinessIds(user.tenant_ids ?? []);
    setIsActive(user.is_active !== false);
    setFormError(null);
    setIsOpen(true);
  };

  const closeModal = () => {
    if (!saving) {
      setIsOpen(false);
    }
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    const trimmedPassword = password.trim();

    if (!trimmedName) return setFormError('El nombre es obligatorio.');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) return setFormError('Email invalido.');
    if (!editingUser && !isStrongPassword(trimmedPassword)) {
      return setFormError('La contrasena debe tener al menos 8 caracteres, mayuscula, minuscula y numero.');
    }
    if (editingUser && trimmedPassword && !isStrongPassword(trimmedPassword)) {
      return setFormError('Si cambias la contrasena, debe tener al menos 8 caracteres, mayuscula, minuscula y numero.');
    }
    if (type === 'Administrador' && businessIds.length === 0) {
      return setFormError('Selecciona al menos un negocio para el administrador.');
    }

    try {
      setSaving(true);
      if (editingUser) {
        await updateGlobalUser(editingUser.id, {
          name: trimmedName,
          email: trimmedEmail,
          user_type: type,
          tenant_ids: type === 'Administrador' ? businessIds : [],
          is_active: isActive,
          ...(trimmedPassword ? { password: trimmedPassword } : {}),
        });
        toast.success('Usuario global actualizado correctamente.');
      } else {
        if (type === 'Backdoor') {
          await createBackdoorUser({
            name: trimmedName,
            email: trimmedEmail,
            password: trimmedPassword,
            user_type: 'Backdoor',
          });
        } else {
          await createAdminUser({
            name: trimmedName,
            email: trimmedEmail,
            password: trimmedPassword,
            user_type: 'Administrador',
            tenant_ids: businessIds,
          });
        }
        toast.success('Usuario global creado correctamente.');
      }
      setIsOpen(false);
      resetForm();
      await fetchAll();
    } catch (err) {
      setFormError(getApiErrorMessage(err, editingUser ? 'No se pudo actualizar el usuario global.' : 'No se pudo crear el usuario global.'));
    } finally {
      setSaving(false);
    }
  };

  const removeGlobalUser = async (user: User) => {
    if (currentUser?.id === user.id) {
      toast.error('No puedes eliminar tu propia cuenta.');
      return;
    }
    const confirmed = window.confirm(`Eliminar el usuario global "${user.name}"? Esta accion no se puede deshacer.`);
    if (!confirmed) return;
    try {
      setDeletingId(user.id);
      await deleteGlobalUser(user.id);
      toast.success('Usuario global eliminado correctamente.');
      await fetchAll();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'No se pudo eliminar el usuario global.'));
    } finally {
      setDeletingId(null);
    }
  };

  if (!authResolved) return <div className="min-h-screen bg-slate-50" />;
  if (!hasToken) return null;

  const businessNamesFor = (user: User): string[] => {
    const ids = user.tenant_ids?.length ? user.tenant_ids : user.business_ids ?? [];
    return ids.map((id) => tenantsById.get(id)?.name ?? id);
  };

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<ShieldCheck className="h-6 w-6" />}
          title="Usuarios globales"
          description="Gestiona administradores con acceso multi-negocio y cuentas backdoor."
          actions={
            <Button leadingIcon={<Plus />} onClick={openCreate}>
              Crear usuario
            </Button>
          }
        />

        {error ? (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {loading ? (
          <EmptyState title="Cargando..." description="Obteniendo usuarios globales." compact />
        ) : (
          <div className="space-y-6">
            <Card
              icon={<UserCog className="h-5 w-5" />}
              title="Administradores"
              description="Tienen acceso a todos los negocios asignados."
              actions={
                <Badge tone="info" label={`${admins.length} ${admins.length === 1 ? 'cuenta' : 'cuentas'}`} variant="soft" />
              }
              padding="sm"
            >
              {admins.length === 0 ? (
                <EmptyState
                  icon={<UserCog />}
                  title="Sin administradores"
                  description="Crea un administrador para que pueda gestionar negocios asignados."
                  compact
                />
              ) : (
                <Table
                  headers={['Administrador', 'Negocios asignados', 'Estado', '']}
                  hasRows={admins.length > 0}
                  emptyMessage="Sin admins."
                  dense
                >
                  {admins.map((user) => {
                    const businesses = businessNamesFor(user);
                    return (
                      <tr key={user.id}>
                        <td className="px-3 py-3 text-sm">
                          <div className="flex items-center gap-3">
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700">
                              {initialsOf(user.name) || 'A'}
                            </span>
                            <div className="min-w-0">
                              <p className="truncate font-medium text-slate-900">{user.name}</p>
                              <p className="truncate text-xs text-slate-500">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-3 py-3 text-sm">
                          {businesses.length === 0 ? (
                            <Badge tone="neutral" label="Sin asignar" variant="dot" />
                          ) : (
                            <div className="flex flex-wrap items-center gap-1.5">
                              {businesses.slice(0, 3).map((name) => (
                                <Badge key={name} tone="info" label={name} variant="soft" size="sm" />
                              ))}
                              {businesses.length > 3 ? (
                                <Badge
                                  tone="neutral"
                                  label={`+${businesses.length - 3}`}
                                  variant="soft"
                                  size="sm"
                                />
                              ) : null}
                            </div>
                          )}
                        </td>
                        <td className="px-3 py-3 text-right text-xs text-slate-500">
                          <Badge tone={user.is_active === false ? 'neutral' : 'success'} label={user.is_active === false ? 'Inactivo' : 'Activo'} variant="dot" size="sm" />
                        </td>
                        <td className="px-3 py-3 text-right text-xs text-slate-500">
                          <div className="flex items-center justify-end gap-1.5">
                            <IconButton icon={<Pencil />} label="Editar" size="sm" variant="ghost" onClick={() => openEdit(user)} />
                            <IconButton icon={<Trash2 />} label="Eliminar" size="sm" variant="danger" onClick={() => void removeGlobalUser(user)} disabled={deletingId === user.id || currentUser?.id === user.id} />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </Table>
              )}
            </Card>

            <Card
              icon={<KeyRound className="h-5 w-5" />}
              title="Backdoors"
              description="Acceso total a la plataforma. Usar solo para soporte y emergencias."
              actions={
                <Badge
                  tone={backdoors.length > 0 ? 'warning' : 'neutral'}
                  label={`${backdoors.length} ${backdoors.length === 1 ? 'cuenta' : 'cuentas'}`}
                  variant="soft"
                />
              }
              padding="sm"
            >
              {backdoors.length === 0 ? (
                <EmptyState
                  icon={<Lock />}
                  title="Sin backdoors"
                  description="No hay cuentas con acceso global ahora mismo."
                  compact
                />
              ) : (
                <Table headers={['Backdoor', 'Acceso', 'Estado', '']} hasRows={backdoors.length > 0} dense>
                  {backdoors.map((user) => (
                    <tr key={user.id}>
                      <td className="px-3 py-3 text-sm">
                        <div className="flex items-center gap-3">
                          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-amber-100 text-xs font-semibold text-amber-700">
                            {initialsOf(user.name) || 'B'}
                          </span>
                          <div className="min-w-0">
                            <p className="truncate font-medium text-slate-900">{user.name}</p>
                            <p className="truncate text-xs text-slate-500">{user.email}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-sm">
                        <Badge tone="warning" label="Acceso global" icon={<KeyRound />} variant="soft" />
                      </td>
                      <td className="px-3 py-3 text-right text-xs text-slate-500">
                        <Badge tone={user.is_active === false ? 'neutral' : 'success'} label={user.is_active === false ? 'Inactivo' : 'Activo'} variant="dot" size="sm" />
                      </td>
                      <td className="px-3 py-3 text-right text-xs text-slate-500">
                        <div className="flex items-center justify-end gap-1.5">
                          <IconButton icon={<Pencil />} label="Editar" size="sm" variant="ghost" onClick={() => openEdit(user)} />
                          <IconButton icon={<Trash2 />} label="Eliminar" size="sm" variant="danger" onClick={() => void removeGlobalUser(user)} disabled={deletingId === user.id || currentUser?.id === user.id} />
                        </div>
                      </td>
                    </tr>
                  ))}
                </Table>
              )}
            </Card>
          </div>
        )}
      </div>

      <Modal
        isOpen={isOpen}
        onClose={closeModal}
        title={editingUser ? 'Editar usuario global' : 'Crear usuario global'}
        description="Configura el tipo de cuenta y su alcance."
        footer={
          <div className="flex items-center justify-end gap-3">
            <Button type="button" variant="secondary" onClick={closeModal} disabled={saving}>
              Cancelar
            </Button>
            <Button type="submit" form="global-user-form" loading={saving} leadingIcon={editingUser ? <Pencil /> : <Plus />}>
              {editingUser ? 'Guardar cambios' : 'Crear usuario'}
            </Button>
          </div>
        }
      >
        <form id="global-user-form" className="space-y-5" onSubmit={submit}>
          {formError ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          ) : null}

          <div>
            <p className="mb-2 text-sm font-medium text-slate-700">Tipo de cuenta</p>
            <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
              <Radio
                variant="card"
                name="user-type"
                label="Administrador"
                description="Gestiona uno o varios negocios asignados."
                checked={type === 'Administrador'}
                onChange={() => setType('Administrador')}
              />
              <Radio
                variant="card"
                name="user-type"
                label="Backdoor"
                description="Acceso global a toda la plataforma."
                checked={type === 'Backdoor'}
                onChange={() => setType('Backdoor')}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Input
              label="Nombre completo"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Doe"
              required
            />
            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@empresa.com"
              required
            />
          </div>

          <Input
            label={editingUser ? 'Nueva contrasena (opcional)' : 'Contrasena'}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimo 8 caracteres con mayuscula, minuscula y numero"
            hint="Debe incluir mayuscula, minuscula y al menos un numero."
            required={!editingUser}
          />

          <Switch
            label="Usuario activo"
            checked={isActive}
            onChange={() => setIsActive((prev) => !prev)}
          />

          {type === 'Administrador' ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <p className="text-sm font-medium text-slate-700">Negocios asignados</p>
                <Badge
                  tone={businessIds.length > 0 ? 'info' : 'neutral'}
                  label={`${businessIds.length}/${tenants.length} seleccionados`}
                  variant="soft"
                />
              </div>
              {tenants.length === 0 ? (
                <EmptyState
                  icon={<Building2 />}
                  title="No hay negocios"
                  description="Crea un negocio antes de asignarlo a un administrador."
                  compact
                />
              ) : (
                <div className="scrollbar-thin grid max-h-72 grid-cols-1 gap-2 overflow-y-auto rounded-2xl border border-slate-200 bg-slate-50/40 p-2 md:grid-cols-2">
                  {tenants.map((tenant) => (
                    <PermissionToggle
                      key={tenant.id}
                      label={tenant.name}
                      description={tenant.slug}
                      icon={<Building2 className="h-4 w-4" />}
                      checked={businessIds.includes(tenant.id)}
                      onChange={() => toggleBusiness(tenant.id)}
                    />
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50/60 p-3">
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700">
                <KeyRound className="h-4 w-4" />
              </span>
              <div className="text-sm text-amber-900">
                <p className="font-semibold">Acceso backdoor</p>
                <p className="mt-0.5 text-amber-800">
                  Esta cuenta tendra acceso total. Usar unicamente para soporte y emergencias.
                </p>
              </div>
            </div>
          )}
        </form>
      </Modal>
    </AppLayout>
  );
}
