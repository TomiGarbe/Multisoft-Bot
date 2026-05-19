import { Cable, Plug } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Card from '@/components/ui/Card';
import EmptyState from '@/components/ui/EmptyState';
import Switch from '@/components/ui/Switch';
import type { IntegrationListItem } from '@/types/integration';

interface IntegrationsSettingsSectionProps {
  items: IntegrationListItem[];
  selectedActionIds: Set<string>;
  mixedActionIds: Set<string>;
  scopeLabel: string;
  loading: boolean;
  saving: boolean;
  onToggle: (actionId: string) => void;
}

function resolveProvider(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.hostname || 'Unknown';
  } catch {
    return 'Unknown';
  }
}

const METHOD_TONE: Record<string, 'info' | 'success' | 'warning' | 'danger' | 'accent' | 'neutral'> = {
  GET: 'info',
  POST: 'success',
  PUT: 'warning',
  PATCH: 'accent',
  DELETE: 'danger',
};

export default function IntegrationsSettingsSection({
  items,
  selectedActionIds,
  mixedActionIds,
  scopeLabel,
  loading,
  saving,
  onToggle,
}: IntegrationsSettingsSectionProps) {
  return (
    <section className="space-y-6">
      <Card
        icon={<Cable className="h-5 w-5" />}
        title="Integraciones"
        description={`Controla integraciones HTTP por canal. Alcance actual: ${scopeLabel}.`}
      >
        <span className="sr-only">Controles de integraciones</span>
      </Card>

      <Card padding="sm">
        {loading ? (
          <p className="px-3 py-6 text-sm text-slate-500">Cargando integraciones...</p>
        ) : !items.length ? (
          <EmptyState
            icon={<Plug />}
            title="Sin integraciones disponibles"
            description="Crea una integracion HTTP en la pestana correspondiente."
          />
        ) : (
          <ul className="divide-y divide-slate-100">
            {items.map((item) => {
              const isSelected = selectedActionIds.has(item.id);
              const isMixed = mixedActionIds.has(item.id);
              return (
                <li
                  key={item.id}
                  className="flex flex-wrap items-center justify-between gap-3 px-3 py-3 transition-colors hover:bg-slate-50/60"
                >
                  <div className="flex min-w-0 flex-1 items-start gap-3">
                    <Badge
                      tone={METHOD_TONE[item.method] ?? 'neutral'}
                      label={item.method}
                      variant="soft"
                      size="sm"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-sm font-medium text-slate-900">{item.name}</p>
                        <Badge
                          tone={item.enabled ? 'success' : 'neutral'}
                          label={item.enabled ? 'Activa' : 'Inactiva'}
                          variant="dot"
                          size="sm"
                        />
                        {isMixed ? (
                          <Badge tone="warning" label="Override mixto" variant="soft" size="sm" />
                        ) : null}
                      </div>
                      <p className="truncate text-xs text-slate-500">
                        {item.description || resolveProvider(item.url)}
                      </p>
                    </div>
                  </div>
                  <Switch
                    layout="inline"
                    label={isSelected ? 'Habilitada' : 'Deshabilitada'}
                    size="sm"
                    checked={isSelected}
                    onChange={() => onToggle(item.id)}
                    disabled={saving || loading}
                  />
                </li>
              );
            })}
          </ul>
        )}
      </Card>
    </section>
  );
}
