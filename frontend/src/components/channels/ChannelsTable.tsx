import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
import { Pencil, Trash } from 'lucide-react';
import type { Channel } from '@/types/channel';

interface Props {
  channels: Channel[];
  isDeletingId: string | null;
  onEdit: (channel: Channel) => void;
  onDelete: (channel: Channel) => void;
}

export default function ChannelsTable({
  channels,
  isDeletingId,
  onEdit,
  onDelete,
}: Props) {
  return (
    <Table
      headers={['Nombre', 'Tipo', 'ID externo', 'Estado', 'Acciones']}
      hasRows={channels.length > 0}
      emptyMessage="No se encontraron canales."
    >
      {channels.map((channel) => (
        <tr key={channel.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">{channel.name}</td>

          <td className="px-4 py-3 text-sm text-slate-700">
            <span className="inline-flex rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-700">
              {channel.type}
            </span>
          </td>

          <td className="px-4 py-3 text-sm text-slate-700">{channel.external_id}</td>

          <td className="px-4 py-3">
            <span
              className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                channel.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-700'
              }`}
            >
              {channel.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </td>

          <td className="px-4 py-3 text-sm">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                className="p-2"
                onClick={() => onEdit(channel)}
                title="Editar"
                aria-label="Editar"
              >
                <Pencil size={16} />
              </Button>

              <Button
                variant="danger"
                className="p-2"
                onClick={() => onDelete(channel)}
                disabled={isDeletingId === channel.id}
                title="Eliminar"
                aria-label="Eliminar"
              >
                <Trash size={16} />
              </Button>
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
