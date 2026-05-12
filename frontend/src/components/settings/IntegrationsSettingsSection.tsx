import Button from '@/components/ui/Button';
import type { IntegrationListItem } from '@/types/integration';

interface IntegrationsSettingsSectionProps {
  items: IntegrationListItem[];
  selectedActionIds: Set<string>;
  mixedActionIds: Set<string>;
  scopeLabel: string;
  loading: boolean;
  saving: boolean;
  dirty: boolean;
  onToggle: (actionId: string) => void;
  onSave: () => void;
}

function resolveProvider(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

export default function IntegrationsSettingsSection({
  items,
  selectedActionIds,
  mixedActionIds,
  scopeLabel,
  loading,
  saving,
  dirty,
  onToggle,
  onSave,
}: IntegrationsSettingsSectionProps) {
  return (
    <section className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Integraciones</h2>
            <p className="mt-1 text-sm text-slate-500">Controla integraciones HTTP por canal. Alcance actual: {scopeLabel}.</p>
          </div>
          <Button onClick={onSave} disabled={!dirty || saving || loading}>
            {saving ? 'Guardando...' : 'Guardar integraciones'}
          </Button>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        {loading ? <p className="text-sm text-slate-500">Cargando integraciones...</p> : null}
        {!loading && !items.length ? <p className="text-sm text-slate-500">No hay integraciones disponibles.</p> : null}
        {!loading && items.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">Integracion</th>
                  <th className="px-2 py-2">Descripcion</th>
                  <th className="px-2 py-2">Metodo</th>
                  <th className="px-2 py-2">Provider</th>
                  <th className="px-2 py-2">Estado global</th>
                  <th className="px-2 py-2">Habilitada en alcance</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const isSelected = selectedActionIds.has(item.id);
                  const isMixed = mixedActionIds.has(item.id);
                  return (
                    <tr key={item.id} className="border-b border-slate-100 align-top">
                      <td className="px-2 py-3 font-medium text-slate-900">{item.name}</td>
                      <td className="px-2 py-3 text-slate-600">{item.description || '-'}</td>
                      <td className="px-2 py-3 text-slate-700">{item.method}</td>
                      <td className="px-2 py-3 text-slate-700">{resolveProvider(item.url)}</td>
                      <td className="px-2 py-3">
                        <span className={`rounded-lg px-2 py-1 text-xs font-semibold ${item.enabled ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                          {item.enabled ? 'Activa' : 'Inactiva'}
                        </span>
                      </td>
                      <td className="px-2 py-3">
                        <label className="inline-flex items-center gap-2 text-sm text-slate-700">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => onToggle(item.id)}
                            disabled={saving || loading}
                          />
                          {isSelected ? 'Habilitada' : 'Deshabilitada'}
                        </label>
                        {isMixed ? <p className="mt-1 text-xs text-amber-700">Override detectado entre canales</p> : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
