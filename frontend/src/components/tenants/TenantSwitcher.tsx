import { Building2, Globe } from 'lucide-react';
import { useTenantContext } from '@/context/tenant-context';

export default function TenantSwitcher() {
  const {
    loading,
    error,
    tenants,
    activeTenantId,
    scope,
    canUseGlobalScope,
    setTenant,
    setScope,
    activeTenant,
  } = useTenantContext();

  if (loading) {
    return <span className="text-xs text-slate-500">Cargando tenant...</span>;
  }

  if (error) {
    return <span className="text-xs text-rose-600">Tenant no disponible</span>;
  }

  if (tenants.length === 0) {
    return <span className="text-xs text-slate-500">Sin tenants asignados</span>;
  }

  return (
    <div className="flex items-center gap-2">
      {canUseGlobalScope && (
        <button
          type="button"
          onClick={() => setScope(scope === 'global' ? 'tenant' : 'global')}
          className={`inline-flex h-9 items-center gap-1 rounded-md border px-2 text-xs font-medium transition ${
            scope === 'global'
              ? 'border-indigo-200 bg-indigo-50 text-indigo-700'
              : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
          }`}
          title="Alternar scope de analytics"
        >
          <Globe className="h-3.5 w-3.5" />
          {scope === 'global' ? 'Global' : 'Tenant'}
        </button>
      )}

      <label className="sr-only" htmlFor="tenant-switcher">
        Tenant activo
      </label>
      <div className="relative">
        <Building2 className="pointer-events-none absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
        <select
          id="tenant-switcher"
          value={activeTenantId ?? ''}
          onChange={(event) => setTenant(event.target.value)}
          className="h-9 min-w-[180px] appearance-none rounded-md border border-slate-200 bg-white pl-8 pr-8 text-sm text-slate-700 shadow-sm focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-100"
        >
          {tenants.map((tenant) => (
            <option key={tenant.id} value={tenant.id}>
              {tenant.name}
            </option>
          ))}
        </select>
      </div>

      <span className="hidden text-xs text-slate-500 md:inline">{activeTenant?.slug}</span>
    </div>
  );
}
