import { Copy, Eye, KeyRound, Power, ShieldCheck, Trash2 } from 'lucide-react';
import { useMemo, useState } from 'react';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import DatePicker from '@/components/ui/DatePicker';
import IconButton from '@/components/ui/IconButton';
import Input from '@/components/ui/Input';
import Select from '@/components/ui/Select';
import Table from '@/components/ui/Table';
import type { Channel } from '@/types/channel';
import type { ApiKeyCreatedItem, ApiKeyItem } from '@/types/apiKey';

interface SecuritySettingsSectionProps {
  channels: Channel[];
  apiKeys: ApiKeyItem[];
  loading: boolean;
  saving: boolean;
  onCreate: (payload: { name: string; channelId?: string; expiresAt?: string }) => Promise<ApiKeyCreatedItem | null>;
  onRegenerate: (apiKey: ApiKeyItem) => Promise<ApiKeyCreatedItem | null>;
  onDeactivate: (apiKeyId: string) => Promise<void>;
  onDelete: (apiKeyId: string) => Promise<void>;
}

function formatDate(value: string | null) {
  if (!value) return '-';
  return new Date(value).toLocaleString();
}

function todayIso(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export default function SecuritySettingsSection({
  channels,
  apiKeys,
  loading,
  saving,
  onCreate,
  onRegenerate,
  onDeactivate,
  onDelete,
}: SecuritySettingsSectionProps) {
  const [name, setName] = useState('');
  const [channelId, setChannelId] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [createdSecret, setCreatedSecret] = useState('');
  const [revealSecret, setRevealSecret] = useState(false);

  const activeCount = useMemo(() => apiKeys.filter((item) => item.is_active).length, [apiKeys]);

  const channelOptions = useMemo(
    () => [
      { value: '', label: 'Todos los canales' },
      ...channels.map((channel) => ({
        value: channel.id,
        label: `${channel.name} (${channel.type})`,
      })),
    ],
    [channels],
  );

  return (
    <section className="space-y-6">
      <Card
        icon={<ShieldCheck className="h-5 w-5" />}
        title="Seguridad"
        description="API Keys webhook, autenticacion de canales y seguridad inbound."
      >
        <div className="text-sm text-slate-600">
          Activas: <Badge tone="success" label={String(activeCount)} variant="soft" />
        </div>
      </Card>

      <Card
        title="Nueva API key webhook"
        description="Las keys pueden ser globales o por canal."
        actions={
          <Button
            disabled={saving || !name.trim()}
            leadingIcon={<KeyRound />}
            onClick={async () => {
              const expiresAtIso = expiresAt
                ? new Date(`${expiresAt}T23:59:59`).toISOString()
                : undefined;
              const created = await onCreate({
                name: name.trim(),
                channelId: channelId || undefined,
                expiresAt: expiresAtIso,
              });
              if (!created) return;
              setCreatedSecret(created.api_key);
              setRevealSecret(true);
              setName('');
              setChannelId('');
              setExpiresAt('');
            }}
          >
            Crear API key
          </Button>
        }
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Input
            label="Nombre"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Webhook inbound"
          />
          <Select
            label="Canal"
            value={channelId}
            onChange={(event) => setChannelId(event.target.value)}
            options={channelOptions}
          />
          <DatePicker
            label="Expira el (opcional)"
            value={expiresAt}
            onChange={setExpiresAt}
            min={todayIso()}
            placeholder="Sin expiracion"
            hint={expiresAt ? undefined : 'Sin expiracion si se deja vacio.'}
          />
        </div>

        {createdSecret ? (
          <div className="mt-4 space-y-2 rounded-xl border border-amber-200 bg-amber-50 p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">
                API key generada (mostrar una sola vez)
              </p>
              <div className="flex items-center gap-1">
                <IconButton
                  icon={<Eye />}
                  label={revealSecret ? 'Ocultar' : 'Mostrar'}
                  size="sm"
                  variant="ghost"
                  onClick={() => setRevealSecret((v) => !v)}
                />
                <IconButton
                  icon={<Copy />}
                  label="Copiar"
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    if (typeof navigator !== 'undefined') {
                      void navigator.clipboard.writeText(createdSecret);
                    }
                  }}
                />
              </div>
            </div>
            <p className="break-all rounded-lg bg-white px-3 py-2 font-mono text-sm text-amber-900 ring-1 ring-amber-200">
              {revealSecret ? createdSecret : '•'.repeat(Math.min(createdSecret.length, 32))}
            </p>
          </div>
        ) : null}
      </Card>

      <Card title="API keys webhook" padding="sm">
        {loading ? (
          <p className="px-2 py-4 text-sm text-slate-500">Cargando API keys...</p>
        ) : (
          <Table
            headers={['Nombre', 'Canal', 'Prefijo', 'Estado', 'Ultimo uso', '']}
            hasRows={apiKeys.length > 0}
            emptyMessage="No hay API keys creadas."
            dense
          >
            {apiKeys.map((item) => (
              <tr key={item.id}>
                <td className="px-3 py-3 text-sm text-slate-800">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-slate-500">
                    Creada: {formatDate(item.created_at)} · Expira: {formatDate(item.expires_at)}
                  </p>
                </td>
                <td className="px-3 py-3 text-sm text-slate-600">
                  {channels.find((channel) => channel.id === item.channel_id)?.name ?? 'Todos los canales'}
                </td>
                <td className="px-3 py-3 font-mono text-xs text-slate-600">{item.key_prefix}</td>
                <td className="px-3 py-3">
                  <Badge
                    tone={item.is_active ? 'success' : 'neutral'}
                    label={item.is_active ? 'Activa' : 'Inactiva'}
                    variant="dot"
                  />
                </td>
                <td className="px-3 py-3 text-sm text-slate-600">{formatDate(item.last_used_at)}</td>
                <td className="px-3 py-3">
                  <div className="flex items-center justify-end gap-1.5">
                    <IconButton
                      icon={<KeyRound />}
                      label="Regenerar"
                      size="sm"
                      variant="ghost"
                      onClick={async () => {
                        const created = await onRegenerate(item);
                        if (created) {
                          setCreatedSecret(created.api_key);
                          setRevealSecret(true);
                        }
                      }}
                      disabled={saving}
                    />
                    <IconButton
                      icon={<Power />}
                      label="Desactivar"
                      size="sm"
                      variant="ghost"
                      onClick={() => void onDeactivate(item.id)}
                      disabled={saving || !item.is_active}
                    />
                    <IconButton
                      icon={<Trash2 />}
                      label="Eliminar"
                      size="sm"
                      variant="danger"
                      onClick={() => void onDelete(item.id)}
                      disabled={saving}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </section>
  );
}
