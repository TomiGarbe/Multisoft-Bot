import { AlertTriangle, Clock3, Pencil, RefreshCw, Trash2, Wifi, WifiOff } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import IconButton from '@/components/ui/IconButton';
import Table from '@/components/ui/Table';
import { CHANNEL_TYPE_LABELS, type ChannelType } from '@/components/channels/channelFormConfig';
import { CHANNEL_PROVIDER_LABELS } from '@/constants/channelProviders';
import type { Channel } from '@/types/channel';

interface Props {
  channels: Channel[];
  isDeletingId: string | null;
  onEdit: (channel: Channel) => void;
  onDelete: (channel: Channel) => void;
}

type ConnectionState = 'connected' | 'disconnected' | 'error' | 'syncing' | 'pending';

const stateConfig: Record<
  ConnectionState,
  { tone: 'success' | 'neutral' | 'danger' | 'info' | 'warning'; icon: React.ReactNode; label: string }
> = {
  connected: { tone: 'success', icon: <Wifi className="h-3 w-3" />, label: 'Conectado' },
  disconnected: { tone: 'neutral', icon: <WifiOff className="h-3 w-3" />, label: 'Desconectado' },
  error: { tone: 'danger', icon: <AlertTriangle className="h-3 w-3" />, label: 'Error' },
  syncing: { tone: 'info', icon: <RefreshCw className="h-3 w-3 animate-spin" />, label: 'Sincronizando' },
  pending: { tone: 'warning', icon: <Clock3 className="h-3 w-3" />, label: 'Pendiente' },
};

function resolveConnectionState(channel: Channel): ConnectionState {
  const raw = typeof channel.config?.connection_status === 'string' ? channel.config.connection_status : '';

  if (raw === 'connected' || raw === 'disconnected' || raw === 'error' || raw === 'syncing' || raw === 'pending') {
    return raw;
  }

  return channel.is_active ? 'connected' : 'disconnected';
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
      headers={['Nombre', 'Tipo', 'Provider', 'Telefono', 'Estado', 'Webhook', 'Ultima sincronizacion', '']}
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
        const cfg = stateConfig[state];

        return (
          <tr key={channel.id}>
            <td className="px-4 py-3 text-sm font-medium text-slate-900">{channel.name}</td>

            <td className="px-4 py-3 text-sm">
              <Badge tone="info" label={resolveTypeLabel(channel.type)} variant="soft" />
            </td>

            <td className="px-4 py-3 text-sm text-slate-600">{provider}</td>
            <td className="px-4 py-3 text-sm text-slate-600">{phone}</td>
            <td className="px-4 py-3 text-sm">
              <Badge tone={cfg.tone} label={cfg.label} icon={cfg.icon} variant="soft" />
            </td>
            <td
              className="max-w-[280px] truncate px-4 py-3 text-sm text-slate-600"
              title={webhook}
            >
              {webhook}
            </td>
            <td className="px-4 py-3 text-sm text-slate-600">{formatDate(lastSync)}</td>

            <td className="px-4 py-3 text-sm">
              <div className="flex items-center justify-end gap-1.5">
                <IconButton
                  icon={<Pencil />}
                  label="Editar"
                  size="sm"
                  variant="ghost"
                  onClick={() => onEdit(channel)}
                />
                <IconButton
                  icon={<Trash2 />}
                  label="Eliminar"
                  size="sm"
                  variant="danger"
                  onClick={() => onDelete(channel)}
                  disabled={isDeletingId === channel.id}
                />
              </div>
            </td>
          </tr>
        );
      })}
    </Table>
  );
}
