import { useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
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

export default function SecuritySettingsSection({ channels, apiKeys, loading, saving, onCreate, onRegenerate, onDeactivate, onDelete }: SecuritySettingsSectionProps) {
  const [name, setName] = useState('');
  const [channelId, setChannelId] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [createdSecret, setCreatedSecret] = useState('');

  const activeCount = useMemo(() => apiKeys.filter((item) => item.is_active).length, [apiKeys]);

  return (
    <section className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <h2 className="text-lg font-semibold text-slate-900">Seguridad</h2>
        <p className="mt-1 text-sm text-slate-500">API Keys webhook, autenticacion de canales y seguridad inbound.</p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-slate-800">Nueva API key webhook</h3>
            <p className="text-sm text-slate-500">Las keys pueden ser globales o por canal. Activas: {activeCount}</p>
          </div>
          <Button
            disabled={saving || !name.trim()}
            onClick={async () => {
              const created = await onCreate({
                name: name.trim(),
                channelId: channelId || undefined,
                expiresAt: expiresAt ? new Date(expiresAt).toISOString() : undefined,
              });
              if (!created) return;
              setCreatedSecret(created.api_key);
              setName('');
              setChannelId('');
              setExpiresAt('');
            }}
          >
            Crear API key
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Nombre</label>
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Webhook inbound" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Canal</label>
            <select value={channelId} onChange={(event) => setChannelId(event.target.value)} className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200">
              <option value="">Todos los canales</option>
              {channels.map((channel) => (
                <option key={channel.id} value={channel.id}>{channel.name} ({channel.type})</option>
              ))}
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Expira en (opcional)</label>
            <input type="datetime-local" value={expiresAt} onChange={(event) => setExpiresAt(event.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
          </div>
        </div>

        {createdSecret ? (
          <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-800">API key generada (mostrar una sola vez)</p>
            <p className="mt-1 break-all font-mono text-sm text-amber-900">{createdSecret}</p>
          </div>
        ) : null}
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <h3 className="mb-4 text-base font-semibold text-slate-800">API keys webhook</h3>
        {loading ? <p className="text-sm text-slate-500">Cargando API keys...</p> : null}
        {!loading && !apiKeys.length ? <p className="text-sm text-slate-500">No hay API keys creadas.</p> : null}
        {!loading && apiKeys.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-2 py-2">Nombre</th>
                  <th className="px-2 py-2">Canal</th>
                  <th className="px-2 py-2">Prefijo</th>
                  <th className="px-2 py-2">Estado</th>
                  <th className="px-2 py-2">Ultimo uso</th>
                  <th className="px-2 py-2">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map((item) => (
                  <tr key={item.id} className="border-b border-slate-100 align-top">
                    <td className="px-2 py-3 text-slate-800">{item.name}</td>
                    <td className="px-2 py-3 text-slate-600">{channels.find((channel) => channel.id === item.channel_id)?.name ?? 'Todos los canales'}</td>
                    <td className="px-2 py-3 font-mono text-slate-600">{item.key_prefix}</td>
                    <td className="px-2 py-3">
                      <span className={`rounded-lg px-2 py-1 text-xs font-semibold ${item.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                        {item.is_active ? 'Activa' : 'Inactiva'}
                      </span>
                    </td>
                    <td className="px-2 py-3 text-slate-600">{formatDate(item.last_used_at)}</td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap gap-2">
                        <Button variant="secondary" disabled={saving} onClick={async () => {
                          const created = await onRegenerate(item);
                          if (created) setCreatedSecret(created.api_key);
                        }}>Regenerar</Button>
                        <Button variant="danger" disabled={saving || !item.is_active} onClick={() => void onDeactivate(item.id)}>Desactivar</Button>
                        <Button variant="ghost" disabled={saving} onClick={() => void onDelete(item.id)}>Eliminar</Button>
                      </div>
                      <p className="mt-1 text-xs text-slate-500">Creada: {formatDate(item.created_at)} | Expira: {formatDate(item.expires_at)}</p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
