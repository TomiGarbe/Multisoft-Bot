import Button from '@/components/ui/Button';
import Table from '@/components/ui/Table';
import { CHANNEL_TYPE_LABELS, type ChannelType } from '@/components/channels/channelFormConfig';
import { CHANNEL_PROVIDER_LABELS } from '@/constants/channelProviders';
import { Pencil, RefreshCw, Trash, Wifi, WifiOff, AlertTriangle, Clock3 } from 'lucide-react';
import type { Channel } from '@/types/channel';

interface Props {
  channels: Channel[];
  isDeletingId: string | null;
  onEdit: (channel: Channel) => void;
  onDelete: (channel: Channel) => void;
}

type ConnectionState = 'connected' | 'disconnected' | 'error' | 'syncing' | 'pending';

const connectionStateStyles: Record<ConnectionState, string> = {
  connected: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  disconnected: 'border-slate-200 bg-slate-100 text-slate-700',
  error: 'border-rose-200 bg-rose-50 text-rose-700',
  syncing: 'border-sky-200 bg-sky-50 text-sky-700',
  pending: 'border-amber-200 bg-amber-50 text-amber-700',
};

const connectionStateLabel: Record<ConnectionState, string> = {
  connected: 'Conectado',
  disconnected: 'Desconectado',
  error: 'Error',
  syncing: 'Sincronizando',
  pending: 'Pendiente',
};

function resolveConnectionState(channel: Channel): ConnectionState {
  const raw = typeof channel.config?.connection_status === 'string' ? channel.config.connection_status : '';

  if (raw === 'connected' || raw === 'disconnected' || raw === 'error' || raw === 'syncing' || raw === 'pending') {
    return raw;
  }

  return channel.is_active ? 'connected' : 'disconnected';
}

function ConnectionStateBadge({ state }: { state: ConnectionState }) {
  const icon = {
    connected: <Wifi size={12} />,
    disconnected: <WifiOff size={12} />,
    error: <AlertTriangle size={12} />,
    syncing: <RefreshCw size={12} className="animate-spin" />,
    pending: <Clock3 size={12} />,
  }[state];

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-xs font-semibold ${connectionStateStyles[state]}`}>
      {icon}
      {connectionStateLabel[state]}
    </span>
  );
}

function resolveTypeLabel(type: string) {
  if (type in CHANNEL_TYPE_LABELS) {
    return CHANNEL_TYPE_LABELS[type as ChannelType];
  }

  return type;
}

function resolveProviderLabel(provider: string) {
  if (provider in CHANNEL_PROVIDER_LABELS) {
    return CHANNEL_PROVIDER_LABELS[provider as keyof typeof CHANNEL_PROVIDER_LABELS];
  }
  return provider;
}

function formatDate(value?: string) {
  if (!value) return '-';
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

export default function ChannelsTable({ channels, isDeletingId, onEdit, onDelete }: Props) {
  return (
    <Table
      headers={['Nombre', 'Tipo', 'Provider', 'Telefono', 'Estado', 'Webhook', 'Ultima sincronizacion', 'Acciones']}
      hasRows={channels.length > 0}
      emptyMessage="No se encontraron canales."
    >
      {channels.map((channel) => {
        const providerRaw = typeof channel.config?.provider === 'string' ? channel.config.provider : '-';
        const provider = providerRaw === '-' ? providerRaw : resolveProviderLabel(providerRaw);
        const webhook = typeof channel.config?.webhook_url === 'string' ? channel.config.webhook_url : '-';
        const lastSync = typeof channel.config?.last_sync_at === 'string' ? channel.config.last_sync_at : undefined;
        const phone = channel.type === 'whatsapp' ? channel.external_id : '-';
        const state = resolveConnectionState(channel);

        return (
          <tr key={channel.id}>
            <td className="px-4 py-3 text-sm font-medium text-slate-900">{channel.name}</td>

            <td className="px-4 py-3 text-sm text-slate-700">
              <span className="inline-flex rounded-full bg-sky-100 px-2.5 py-1 text-xs font-semibold text-sky-700">
                {resolveTypeLabel(channel.type)}
              </span>
            </td>

            <td className="px-4 py-3 text-sm text-slate-700">{provider}</td>
            <td className="px-4 py-3 text-sm text-slate-700">{phone}</td>
            <td className="px-4 py-3 text-sm"><ConnectionStateBadge state={state} /></td>
            <td className="max-w-[280px] truncate px-4 py-3 text-sm text-slate-700" title={webhook}>{webhook}</td>
            <td className="px-4 py-3 text-sm text-slate-700">{formatDate(lastSync)}</td>

            <td className="px-4 py-3 text-sm">
              <div className="flex items-center gap-2">
                <Button variant="secondary" className="p-2" onClick={() => onEdit(channel)} title="Editar" aria-label="Editar">
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
        );
      })}
    </Table>
  );
}

