import { Pencil, PlayCircle, Power, Trash2 } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import IconButton from '@/components/ui/IconButton';
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

function methodTone(method: string): 'info' | 'success' | 'warning' | 'danger' | 'accent' | 'neutral' {
  switch (method) {
    case 'GET':
      return 'info';
    case 'POST':
      return 'success';
    case 'PUT':
      return 'warning';
    case 'PATCH':
      return 'accent';
    case 'DELETE':
      return 'danger';
    default:
      return 'neutral';
  }
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
      headers={['Nombre', 'Metodo', 'URL', 'Estado', 'Auth', 'Canal', 'Actualizado', '']}
      hasRows={items.length > 0}
      emptyMessage="No se encontraron integraciones."
    >
      {items.map((item) => (
        <tr key={item.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{item.name}</td>
          <td className="px-4 py-3 text-sm">
            <Badge tone={methodTone(item.method)} label={item.method} variant="soft" />
          </td>
          <td className="max-w-[280px] truncate px-4 py-3 text-sm text-slate-600" title={item.url}>
            <code className="font-mono text-xs">{item.url}</code>
          </td>
          <td className="px-4 py-3 text-sm">
            <Badge
              tone={item.enabled ? 'success' : 'neutral'}
              label={item.enabled ? 'Activo' : 'Inactivo'}
              variant="dot"
            />
          </td>
          <td className="px-4 py-3 text-sm text-slate-600">{authLabel(item.url)}</td>
          <td className="px-4 py-3 text-sm text-slate-500">Global</td>
          <td className="px-4 py-3 text-sm text-slate-600">{formatDate(item.updated_at)}</td>
          <td className="px-4 py-3">
            <div className="flex items-center justify-end gap-1.5">
              <IconButton
                icon={<Pencil />}
                label="Editar"
                size="sm"
                variant="ghost"
                onClick={() => onEdit(item.id)}
                disabled={!canUpdate || workingId === item.id}
              />
              <IconButton
                icon={<Power />}
                label={item.enabled ? 'Desactivar' : 'Activar'}
                size="sm"
                variant="ghost"
                onClick={() => onToggle(item)}
                disabled={!canUpdate || workingId === item.id}
              />
              <IconButton
                icon={<PlayCircle />}
                label="Probar integracion"
                size="sm"
                variant="ghost"
                onClick={() => onTest(item.id)}
                disabled={!canUpdate || workingId === item.id}
              />
              <IconButton
                icon={<Trash2 />}
                label="Eliminar"
                size="sm"
                variant="danger"
                onClick={() => onDelete(item)}
                disabled={!canDelete || workingId === item.id}
              />
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
