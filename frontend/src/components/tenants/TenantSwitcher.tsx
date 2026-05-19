import { Building2 } from 'lucide-react';
import { useTenantContext } from '@/context/tenant-context';
import Select from '@/components/ui/Select';

export default function TenantSwitcher() {
  const { loading, error, tenants, activeTenantId, setTenant, canSwitchTenant } = useTenantContext();

  if (loading) {
    return null;
  }

  if (error) {
    return null;
  }

  if (tenants.length === 0) {
    return null;
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
        searchable={tenants.length >= 8}
      />
    </div>
  );
}
