import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import type { Channel } from '@/types/channel';
import type { ChannelConfigValidationStatus } from '@/types/channelConfig';
import type { ChannelSettingsEditable, UserTypesEditable } from '@/types/settings';

interface ChannelSettingsSectionProps {
  channel: Channel | null;
  value: ChannelSettingsEditable;
  userTypes: UserTypesEditable;
  status: ChannelConfigValidationStatus;
  missingFields: string[];
  isDirty: boolean;
  saving: boolean;
  onSave: () => void;
  onChannelSettingsChange: (patch: Partial<ChannelSettingsEditable>) => void;
  onUserTypesChange: (next: UserTypesEditable) => void;
}

export default function ChannelSettingsSection({
  channel,
  value,
  userTypes,
  status,
  missingFields,
  isDirty,
  saving,
  onSave,
  onChannelSettingsChange,
  onUserTypesChange,
}: ChannelSettingsSectionProps) {
  if (!channel) {
    return (
      <section className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
        Canal no configurado. Conecta un canal para editar su configuracion.
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Canales</h2>
            <p className="text-sm text-slate-500">Ajustes especificos para {channel.name}.</p>
          </div>
          <Button onClick={onSave} disabled={!isDirty || saving}>{saving ? 'Guardando...' : 'Guardar canal'}</Button>
        </div>

        <div className="mb-4 flex flex-wrap gap-2 text-xs font-semibold">
          <span className={`rounded-lg border px-3 py-1 ${status.is_valid ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-800'}`}>
            {status.is_valid ? 'Configuracion valida' : 'Configuracion incompleta'}
          </span>
          {!status.is_valid && missingFields.length > 0 ? (
            <span className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 text-amber-800">Falta: {missingFields.join(', ')}</span>
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input label="Maximo de mensajes del bot" value={String(value.max_bot_messages)} onChange={(event) => onChannelSettingsChange({ max_bot_messages: Number(event.target.value) || 0 })} />
          <Input label="Horas para reset humano" value={String(value.human_handoff_reset_hours)} onChange={(event) => onChannelSettingsChange({ human_handoff_reset_hours: Number(event.target.value) || 0 })} />
          <div className="space-y-1.5 md:col-span-2">
            <label className="block text-sm font-medium text-slate-700">Respuesta automatica al derivar</label>
            <textarea value={value.max_bot_messages_message} onChange={(event) => onChannelSettingsChange({ max_bot_messages_message: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
          </div>
          <div className="space-y-1.5 md:col-span-2">
            <label className="block text-sm font-medium text-slate-700">Respuesta contenido no soportado</label>
            <textarea value={value.unsupported_content_message} onChange={(event) => onChannelSettingsChange({ unsupported_content_message: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-800">Tipos de usuario</h3>
          <Button
            variant="secondary"
            onClick={() => onUserTypesChange({ ...userTypes, types: [...userTypes.types, { key: `type_${userTypes.types.length + 1}`, label: '', color: '#2563eb', is_default: false }] })}
          >
            Agregar tipo
          </Button>
        </div>
        <div className="space-y-3">
          {userTypes.types.map((userType, index) => (
            <div key={userType.key || `user-type-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_140px_140px_auto]">
              <Input
                label="Label"
                value={userType.label}
                onChange={(event) => {
                  const next = [...userTypes.types];
                  next[index] = { ...next[index], label: event.target.value };
                  onUserTypesChange({ ...userTypes, types: next });
                }}
              />
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-slate-700">Color</label>
                <input type="color" value={userType.color} onChange={(event) => { const next = [...userTypes.types]; next[index] = { ...next[index], color: event.target.value }; onUserTypesChange({ ...userTypes, types: next }); }} className="h-10 w-full rounded-lg border border-slate-300" />
              </div>
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-slate-700">Default</label>
                <Button
                  variant={userType.is_default ? 'primary' : 'secondary'}
                  onClick={() => {
                    const next = userTypes.types.map((item, currentIndex) => ({ ...item, is_default: currentIndex === index }));
                    onUserTypesChange({ ...userTypes, types: next, default_type: next[index].key });
                  }}
                >
                  {userType.is_default ? 'Seleccionado' : 'Seleccionar'}
                </Button>
              </div>
              <div className="flex items-end">
                <Button
                  variant="danger"
                  onClick={() => onUserTypesChange({ ...userTypes, types: userTypes.types.filter((_, currentIndex) => currentIndex !== index) })}
                >
                  Eliminar
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
