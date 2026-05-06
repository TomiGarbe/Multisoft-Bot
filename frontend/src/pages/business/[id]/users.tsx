import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Table from '@/components/ui/Table';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { getApiErrorMessage } from '@/services/api';
import { getToken } from '@/services/auth';
import { getRoles } from '@/services/roles';
import { createBusinessUser, getBusinessUsers } from '@/services/users';
import type { Role, User } from '@/types/access';

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

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      setSaving(true);
      await createBusinessUser(businessId, {
        name,
        email,
        password,
        role_id: roleId || null,
        user_type: 'BUSINESS_USER',
      });
      toast.success('Usuario del negocio creado correctamente.');
      setIsOpen(false);
      setName(''); setEmail(''); setPassword(''); setRoleId('');
      await fetchAll();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'No se pudo crear el usuario del negocio.'));
    } finally {
      setSaving(false);
    }
  };

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader title="Usuarios del negocio" description={`Business ID: ${businessId}`} actions={<Button onClick={() => setIsOpen(true)}>+ Crear</Button>} />
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        {loading ? <div className="text-sm text-slate-500">Cargando...</div> : (
          <Table headers={['Nombre', 'Email', 'Rol']} hasRows={users.length > 0} emptyMessage="Sin usuarios.">
            {users.map((u) => <tr key={u.id}><td className="px-4 py-3 text-sm">{u.name}</td><td className="px-4 py-3 text-sm">{u.email}</td><td className="px-4 py-3 text-sm">{u.role?.name ?? '-'}</td></tr>)}
          </Table>
        )}
      </div>
      <Modal isOpen={isOpen} title="Crear usuario del negocio" onClose={() => !saving && setIsOpen(false)} footer={<Button type="submit" form="business-user-form" disabled={saving}>Crear</Button>}>
        <form id="business-user-form" className="space-y-4" onSubmit={submit}>
          <Input label="Nombre" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <div className="space-y-1 text-sm"><label>Rol</label><select value={roleId} onChange={(e) => setRoleId(e.target.value)} className="w-full rounded border border-slate-300 px-2 py-1"><option value="">Sin rol</option>{roles.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}</select></div>
        </form>
      </Modal>
    </AppLayout>
  );
}
