import Button from '@/components/ui/Button';
import Table from '@/components/ui/Table';
import type { IntegrationListItem } from '@/types/integration';

interface IntegrationsTableProps {
  items: IntegrationListItem[];
  workingId: string | null;
  canUpdate: boolean;
  canDelete: boolean;
  onEdit: (id: string) => void;
  onToggle: (item: IntegrationListItem) => void;
  onTest: (id: string) => void;
  onDelete: (item: IntegrationListItem) => void;
}

function authLabel(url: string): string {
  const hasQueryKey = url.includes('apikey=') || url.includes('api_key=');
  return hasQueryKey ? 'API key/query' : 'Configurable';
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return new Intl.DateTimeFormat('es-AR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

export default function IntegrationsTable({
  items,
  workingId,
  canUpdate,
  canDelete,
  onEdit,
  onToggle,
  onTest,
  onDelete,
}: IntegrationsTableProps) {
  return (
    <Table
      headers={['Nombre', 'Metodo', 'URL', 'Estado', 'Auth', 'Canal', 'Actualizado', 'Acciones']}
      hasRows={items.length > 0}
      emptyMessage="No se encontraron integraciones."
    >
      {items.map((item) => (
        <tr key={item.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{item.name}</td>
          <td className="px-4 py-3 text-sm text-slate-700">{item.method}</td>
          <td className="max-w-[260px] truncate px-4 py-3 text-sm text-slate-700" title={item.url}>{item.url}</td>
          <td className="px-4 py-3 text-sm">
            <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${item.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
              {item.enabled ? 'Activo' : 'Inactivo'}
            </span>
          </td>
          <td className="px-4 py-3 text-sm text-slate-700">{authLabel(item.url)}</td>
          <td className="px-4 py-3 text-sm text-slate-500">Global</td>
          <td className="px-4 py-3 text-sm text-slate-700">{formatDate(item.updated_at)}</td>
          <td className="px-4 py-3">
            <div className="flex items-center gap-2">
              <Button variant="secondary" className="px-2 py-1 text-xs" onClick={() => onEdit(item.id)} disabled={!canUpdate || workingId === item.id}>Editar</Button>
              <Button variant="secondary" className="px-2 py-1 text-xs" onClick={() => onToggle(item)} disabled={!canUpdate || workingId === item.id}>
                {item.enabled ? 'Desactivar' : 'Activar'}
              </Button>
              <Button variant="secondary" className="px-2 py-1 text-xs" onClick={() => onTest(item.id)} disabled={!canUpdate || workingId === item.id}>Probar</Button>
              <Button variant="danger" className="px-2 py-1 text-xs" onClick={() => onDelete(item)} disabled={!canDelete || workingId === item.id}>Eliminar</Button>
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
