import { Building2 } from 'lucide-react';
import { useTenantContext } from '@/context/tenant-context';
import Select from '@/components/ui/Select';

export default function TenantSwitcher() {
  const { loading, error, tenants, activeTenantId, setTenant, canSwitchTenant, isSuperAdmin } = useTenantContext();

  if (loading) {
    return <span className="text-xs text-slate-500">Cargando tenant...</span>;
  }

  if (error) {
    return <span className="text-xs text-rose-600">Tenant no disponible</span>;
  }

  if (tenants.length === 0) {
    return <span className="text-xs text-slate-500">Sin tenants asignados</span>;
  }

  if (!canSwitchTenant) {
    return null;
  }

  return (
    <div className="w-full max-w-[260px] min-w-[180px]">
      <Select
        id="tenant-switcher"
        value={activeTenantId ?? ''}
        onChange={(event) => setTenant(event.target.value)}
        options={tenants.map((tenant) => ({ value: tenant.id, label: tenant.name }))}
        leadingIcon={<Building2 className="h-4 w-4" />}
        placeholder={isSuperAdmin ? 'Selecciona un tenant' : undefined}
      />
    </div>
  );
}
