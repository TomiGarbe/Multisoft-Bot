import Table from '@/components/ui/Table';
import Button from '@/components/ui/Button';
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
      headers={['Name', 'Type', 'External ID', 'Status', 'Actions']}
      hasRows={channels.length > 0}
      emptyMessage="No channels found. Create your first channel to get started."
    >
      {channels.map((channel) => (
        <tr key={channel.id}>
          <td className="px-4 py-3 text-sm font-medium text-slate-900">
            {channel.name}
          </td>

          <td className="px-4 py-3 text-sm text-slate-700">
            <span className="inline-flex rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-700">
              {channel.type}
            </span>
          </td>

          <td className="px-4 py-3 text-sm text-slate-700">
            {channel.external_id}
          </td>

          <td className="px-4 py-3">
            <span
              className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                channel.is_active
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-slate-200 text-slate-700'
              }`}
            >
              {channel.is_active ? 'Active' : 'Inactive'}
            </span>
          </td>

          <td className="px-4 py-3 text-sm">
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                className="px-3 py-1.5"
                onClick={() => onEdit(channel)}
              >
                Edit
              </Button>

              <Button
                variant="danger"
                className="px-3 py-1.5"
                onClick={() => onDelete(channel)}
                disabled={isDeletingId === channel.id}
              >
                {isDeletingId === channel.id ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </td>
        </tr>
      ))}
    </Table>
  );
}
