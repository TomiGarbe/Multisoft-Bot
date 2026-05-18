import { ArrowLeft, Plus, ShieldCheck, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import EmptyState from '@/components/ui/EmptyState';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Select from '@/components/ui/Select';
import Table from '@/components/ui/Table';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { getApiErrorMessage } from '@/services/api';
import { getToken } from '@/services/auth';
import { getRoles } from '@/services/roles';
import { createBusinessUser, getBusinessUsers } from '@/services/users';
import type { Role, User } from '@/types/access';

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

export default function BusinessUsersPage() {
  const toast = useToast();
  const router = useRouter();
  const businessId = String(router.query.id ?? '');
  const hasToken = Boolean(getToken());
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [roleId, setRoleId] = useState('');

  const fetchAll = async () => {
    if (!businessId) return;
    try {
      setLoading(true);
      setError(null);
      const [businessUsers, roleList] = await Promise.all([getBusinessUsers(businessId), getRoles()]);
      setUsers(businessUsers);
      setRoles(roleList);
    } catch (err) {
      setError(getApiErrorMessage(err, 'No se pudieron cargar los usuarios del negocio.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hasToken && businessId) void fetchAll();
  }, [hasToken, businessId]);

  const resetForm = () => {
    setName('');
    setEmail('');
    setPassword('');
    setRoleId('');
    setFormError(null);
  };

  const openCreate = () => {
    resetForm();
    setIsOpen(true);
  };

  const closeModal = () => {
    if (!saving) setIsOpen(false);
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFormError(null);

    const trimmedName = name.trim();
    const trimmedEmail = email.trim();
    const trimmedPassword = password.trim();

    if (!trimmedName) return setFormError('El nombre es obligatorio.');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) return setFormError('Email invalido.');
    if (!isStrongPassword(trimmedPassword)) {
      return setFormError(
        'La contrasena debe tener al menos 8 caracteres, mayuscula, minuscula y numero.',
      );
    }

    try {
      setSaving(true);
      await createBusinessUser(businessId, {
        name: trimmedName,
        email: trimmedEmail,
        password: trimmedPassword,
        role_id: roleId || null,
        user_type: 'User',
      });
      toast.success('Usuario del negocio creado correctamente.');
      setIsOpen(false);
      resetForm();
      await fetchAll();
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'No se pudo crear el usuario del negocio.'));
    } finally {
      setSaving(false);
    }
  };

  if (!hasToken) return null;

  const selectedRole = roles.find((role) => role.id === roleId) ?? null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader
          icon={<Users className="h-6 w-6" />}
          title="Usuarios del negocio"
          description={`Gestiona usuarios asignados al negocio ${businessId}.`}
          breadcrumb={
            <button
              type="button"
              onClick={() => router.back()}
              className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 transition-colors hover:text-slate-800"
            >
              <ArrowLeft className="h-3 w-3" /> Volver
            </button>
          }
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
          <EmptyState title="Cargando..." description="Obteniendo usuarios del negocio." compact />
        ) : (
          <Card
            icon={<Users className="h-5 w-5" />}
            title="Usuarios"
            description="Cuentas con acceso a este negocio."
            actions={
              <Badge
                tone="info"
                label={`${users.length} ${users.length === 1 ? 'cuenta' : 'cuentas'}`}
                variant="soft"
              />
            }
            padding="sm"
          >
            {users.length === 0 ? (
              <EmptyState
                icon={<Users />}
                title="Sin usuarios"
                description="Crea el primer usuario del negocio."
                compact
              />
            ) : (
              <Table headers={['Usuario', 'Rol', '']} hasRows={users.length > 0} dense>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-3 py-3 text-sm">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700">
                          {initialsOf(user.name) || 'U'}
                        </span>
                        <div className="min-w-0">
                          <p className="truncate font-medium text-slate-900">{user.name}</p>
                          <p className="truncate text-xs text-slate-500">{user.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3 text-sm">
                      {user.role?.name ? (
                        <Badge tone="info" label={user.role.name} variant="soft" />
                      ) : (
                        <Badge tone="neutral" label="Sin rol" variant="dot" />
                      )}
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Badge tone="success" label="Activo" variant="dot" size="sm" />
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Card>
        )}
      </div>

      <Modal
        isOpen={isOpen}
        title="Crear usuario del negocio"
        description="Configura los accesos del nuevo usuario."
        onClose={closeModal}
        footer={
          <div className="flex items-center justify-end gap-3">
            <Button type="button" variant="secondary" onClick={closeModal} disabled={saving}>
              Cancelar
            </Button>
            <Button type="submit" form="business-user-form" loading={saving} leadingIcon={<Plus />}>
              Crear usuario
            </Button>
          </div>
        }
      >
        <form id="business-user-form" className="space-y-5" onSubmit={submit}>
          {formError ? (
            <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {formError}
            </div>
          ) : null}

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
            label="Contrasena"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimo 8 caracteres con mayuscula, minuscula y numero"
            hint="Debe incluir mayuscula, minuscula y al menos un numero."
            required
          />

          <Select
            label="Rol"
            value={roleId}
            onChange={(event) => setRoleId(event.target.value)}
            options={roles.map((role) => ({
              value: role.id,
              label: role.name,
              description: role.description ?? undefined,
              icon: <ShieldCheck className="h-4 w-4" />,
            }))}
            placeholder="Sin rol"
            searchable={roles.length > 6}
            hint={selectedRole?.description ?? undefined}
          />
        </form>
      </Modal>
    </AppLayout>
  );
}
