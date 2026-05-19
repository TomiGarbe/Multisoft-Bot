import { AlertTriangle, CheckCircle2, Plus, Radio as RadioIcon, Tag, Trash2, Users } from 'lucide-react';
import Badge from '@/components/ui/Badge';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import ColorPicker from '@/components/ui/ColorPicker';
import IconButton from '@/components/ui/IconButton';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
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
      <Card
        className="border-amber-200 bg-amber-50/70"
        icon={<AlertTriangle className="h-5 w-5 text-amber-600" />}
        title="Canal no configurado"
        description="Conecta un canal para editar su configuracion."
      >
        <span className="sr-only">Estado del canal</span>
      </Card>
    );
  }

  return (
    <section className="space-y-6">
      <Card
        icon={<RadioIcon className="h-5 w-5" />}
        title="Canales"
        description={`Ajustes especificos para ${channel.name}.`}
        actions={
          <Button onClick={onSave} loading={saving} disabled={!isDirty}>
            Guardar canal
          </Button>
        }
      >
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge
            tone={status.is_valid ? 'success' : 'warning'}
            label={status.is_valid ? 'Configuracion valida' : 'Configuracion incompleta'}
            icon={
              status.is_valid ? (
                <CheckCircle2 className="h-3 w-3" />
              ) : (
                <AlertTriangle className="h-3 w-3" />
              )
            }
            variant="soft"
          />
          {!status.is_valid && missingFields.length > 0 ? (
            <Badge tone="warning" label={`Falta: ${missingFields.join(', ')}`} variant="outline" />
          ) : null}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Maximo de mensajes del bot"
            value={String(value.max_bot_messages)}
            onChange={(event) =>
              onChannelSettingsChange({ max_bot_messages: Number(event.target.value) || 0 })
            }
          />
          <Input
            label="Horas para reset humano"
            value={String(value.human_handoff_reset_hours)}
            onChange={(event) =>
              onChannelSettingsChange({
                human_handoff_reset_hours: Number(event.target.value) || 0,
              })
            }
          />
          <div className="md:col-span-2">
            <Textarea
              label="Respuesta automatica al derivar"
              value={value.max_bot_messages_message}
              onChange={(event) => onChannelSettingsChange({ max_bot_messages_message: event.target.value })}
              rows={3}
            />
          </div>
          <div className="md:col-span-2">
            <Textarea
              label="Respuesta contenido no soportado"
              value={value.unsupported_content_message}
              onChange={(event) =>
                onChannelSettingsChange({ unsupported_content_message: event.target.value })
              }
              rows={3}
            />
          </div>
        </div>
      </Card>

      <Card
        icon={<Users className="h-5 w-5" />}
        title="Tipos de usuario"
        description="Define las categorias de usuario que reconoce el bot."
        actions={
          <Button
            variant="secondary"
            leadingIcon={<Plus />}
            onClick={() =>
              onUserTypesChange({
                ...userTypes,
                types: [
                  ...userTypes.types,
                  {
                    key: `type_${userTypes.types.length + 1}`,
                    label: '',
                    color: '#2563eb',
                    is_default: false,
                  },
                ],
              })
            }
          >
            Agregar tipo
          </Button>
        }
      >
        <div className="space-y-3">
          {userTypes.types.map((userType, index) => (
            <div
              key={userType.key || `user-type-${index}`}
              className="grid grid-cols-1 items-end gap-3 rounded-xl border border-slate-200 bg-slate-50/50 p-3 md:grid-cols-[1fr_120px_160px_auto]"
            >
              <Input
                label="Label"
                value={userType.label}
                onChange={(event) => {
                  const next = [...userTypes.types];
                  next[index] = { ...next[index], label: event.target.value };
                  onUserTypesChange({ ...userTypes, types: next });
                }}
                leadingIcon={<Tag className="h-4 w-4" />}
              />
              <ColorPicker
                label="Color"
                value={userType.color}
                onChange={(nextColor) => {
                  const next = [...userTypes.types];
                  next[index] = { ...next[index], color: nextColor };
                  onUserTypesChange({ ...userTypes, types: next });
                }}
              />
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-slate-700">Default</label>
                <Button
                  variant={userType.is_default ? 'primary' : 'secondary'}
                  size="md"
                  className="w-full"
                  onClick={() => {
                    const next = userTypes.types.map((item, currentIndex) => ({
                      ...item,
                      is_default: currentIndex === index,
                    }));
                    onUserTypesChange({ ...userTypes, types: next, default_type: next[index].key });
                  }}
                >
                  {userType.is_default ? 'Seleccionado' : 'Marcar default'}
                </Button>
              </div>
              <div className="flex items-end justify-end">
                <IconButton
                  icon={<Trash2 />}
                  label="Eliminar tipo"
                  variant="danger"
                  onClick={() =>
                    onUserTypesChange({
                      ...userTypes,
                      types: userTypes.types.filter((_, currentIndex) => currentIndex !== index),
                    })
                  }
                />
              </div>
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
}
