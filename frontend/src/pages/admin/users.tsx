import { useEffect, useMemo, useState } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import PageHeader from '@/components/ui/PageHeader';
import Table from '@/components/ui/Table';
import { ToastViewport, useToast } from '@/components/ui/toast';
import { getApiErrorMessage, TENANT_CONTEXT_CHANGED_EVENT } from '@/services/api';
import { getToken } from '@/services/auth';
import { getTenants } from '@/services/tenants';
import { createAdminUser, createBackdoorUser, getGlobalUsers } from '@/services/users';
import type { User } from '@/types/access';
import type { Tenant } from '@/types/tenant';

export default function GlobalUsersPage() {
  const toast = useToast();
  const hasToken = Boolean(getToken());
  const [users, setUsers] = useState<User[]>([]);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [type, setType] = useState<'ADMIN' | 'BACKDOOR'>('ADMIN');
  const [businessIds, setBusinessIds] = useState<string[]>([]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [globalUsers, tenantList] = await Promise.all([getGlobalUsers(), getTenants()]);
      setUsers(globalUsers);
      setTenants(tenantList);
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

  const admins = useMemo(() => users.filter((u) => u.user_type === 'ADMIN'), [users]);
  const backdoors = useMemo(() => users.filter((u) => u.user_type === 'BACKDOOR'), [users]);

  const toggleBusiness = (businessId: string) => {
    setBusinessIds((prev) => (prev.includes(businessId) ? prev.filter((id) => id !== businessId) : [...prev, businessId]));
  };

  const submit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      setSaving(true);
      if (type === 'BACKDOOR') {
        await createBackdoorUser({ name, email, password, user_type: 'BACKDOOR' });
      } else {
        await createAdminUser({ name, email, password, user_type: 'ADMIN', business_ids: businessIds });
      }
      toast.success('Usuario global creado correctamente.');
      setIsOpen(false);
      setName(''); setEmail(''); setPassword(''); setBusinessIds([]); setType('ADMIN');
      await fetchAll();
    } catch (err) {
      toast.error(getApiErrorMessage(err, 'No se pudo crear el usuario global.'));
    } finally {
      setSaving(false);
    }
  };

  if (!hasToken) return null;

  return (
    <AppLayout>
      <ToastViewport toasts={toast.items} onClose={toast.remove} />
      <div className="space-y-6 p-6 md:p-8">
        <PageHeader title="Usuarios globales" description="Admins y Backdoors" actions={<Button onClick={() => setIsOpen(true)}>+ Crear</Button>} />
        {error && <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}
        {loading ? <div className="text-sm text-slate-500">Cargando...</div> : (
          <div className="space-y-6">
            <Table headers={['Admin', 'Email', 'Negocios']} hasRows={admins.length > 0} emptyMessage="Sin admins.">
              {admins.map((u) => <tr key={u.id}><td className="px-4 py-3 text-sm">{u.name}</td><td className="px-4 py-3 text-sm">{u.email}</td><td className="px-4 py-3 text-sm">{u.business_ids?.length ?? 0}</td></tr>)}
            </Table>
            <Table headers={['Backdoor', 'Email', 'Acceso']} hasRows={backdoors.length > 0} emptyMessage="Sin backdoors.">
              {backdoors.map((u) => <tr key={u.id}><td className="px-4 py-3 text-sm">{u.name}</td><td className="px-4 py-3 text-sm">{u.email}</td><td className="px-4 py-3 text-sm">Global</td></tr>)}
            </Table>
          </div>
        )}
      </div>
      <Modal isOpen={isOpen} title="Crear usuario global" onClose={() => !saving && setIsOpen(false)} footer={<Button type="submit" form="global-user-form" disabled={saving}>Crear</Button>}>
        <form id="global-user-form" className="space-y-4" onSubmit={submit}>
          <Input label="Nombre" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <div className="space-y-1 text-sm"><label>Tipo</label><select value={type} onChange={(e) => setType(e.target.value as 'ADMIN'|'BACKDOOR')} className="w-full rounded border border-slate-300 px-2 py-1"><option value="ADMIN">ADMIN</option><option value="BACKDOOR">BACKDOOR</option></select></div>
          {type === 'ADMIN' && <div className="max-h-40 space-y-1 overflow-auto rounded border border-slate-200 p-2">{tenants.map((t) => <label key={t.id} className="block text-sm"><input type="checkbox" checked={businessIds.includes(t.id)} onChange={() => toggleBusiness(t.id)} /> {t.name}</label>)}</div>}
        </form>
      </Modal>
    </AppLayout>
  );
}
