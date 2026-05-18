import { useEffect, useMemo, useState } from 'react';
import { Bot, FileText, Hash, Layers, ListChecks, Plus, Settings2, Trash2 } from 'lucide-react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Checkbox from '@/components/ui/Checkbox';
import IconButton from '@/components/ui/IconButton';
import Input from '@/components/ui/Input';
import MultiSelect from '@/components/ui/MultiSelect';
import Select from '@/components/ui/Select';
import Switch from '@/components/ui/Switch';
import Textarea from '@/components/ui/Textarea';
import type {
  BotConfigEditable,
  ConfigSection,
  CustomFieldConfig,
  CustomFieldType,
} from '@/types/channelConfig';
import type { ChannelSettingsEditable, UserTypesEditable } from '@/types/settings';

interface GeneralSettingsSectionProps {
  scopeLabel: string;
  channelSettings: ChannelSettingsEditable;
  userTypes: UserTypesEditable;
  botConfig: BotConfigEditable;
  onChannelSettingsChange: (patch: Partial<ChannelSettingsEditable>) => void;
  onUserTypesChange: (next: UserTypesEditable) => void;
  onBotConfigChange: (next: BotConfigEditable) => void;
  onSaveChannelConfig: () => void;
  isChannelDirty: boolean;
  savingChannel: boolean;
  statusText: string;
}

const CUSTOM_FIELD_TYPES: { value: CustomFieldType; label: string }[] = [
  { value: 'short_text', label: 'Texto corto' },
  { value: 'long_text', label: 'Texto largo' },
  { value: 'list', label: 'Lista' },
  { value: 'group', label: 'Grupo' },
  { value: 'group_list', label: 'Lista de grupos' },
];

const OBJECTIVES_ENTRY_TEMPLATE: Record<string, unknown> = {
  id: '',
  name: '',
  enabled: true,
  applies_to: ['{{user.type}}'],
  objective: '',
  description: '',
  success_condition: '',
  guidelines: [],
  rules: [],
};

const DATA_COLLECTION_ENTRY_TEMPLATE: Record<string, unknown> = {
  id: '',
  name: '',
  enabled: true,
  applies_to: ['{{user.type}}'],
  display_field: '',
  fields: [],
};

const DATA_COLLECTION_FIELD_TEMPLATE: Record<string, unknown> = {
  key: '',
  label: '',
  type: 'text',
  description: '',
  examples: [],
  required: false,
  validation_hint: '',
  is_name_field: false,
};

function toLabel(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

function toStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function toObject(value: unknown): Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function toEntries(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.filter(
        (item): item is Record<string, unknown> =>
          typeof item === 'object' && item !== null && !Array.isArray(item),
      )
    : [];
}

function sanitizeCustomField(raw: unknown): CustomFieldConfig {
  const value = toObject(raw);
  return {
    key: typeof value.key === 'string' ? value.key : '',
    label: typeof value.label === 'string' ? value.label : '',
    type:
      value.type === 'short_text' ||
      value.type === 'long_text' ||
      value.type === 'list' ||
      value.type === 'group' ||
      value.type === 'group_list'
        ? value.type
        : 'short_text',
    description: typeof value.description === 'string' ? value.description : '',
    required: Boolean(value.required),
    options: toStringArray(value.options),
    fields: Array.isArray(value.fields) ? value.fields.map(sanitizeCustomField) : [],
    item_fields: Array.isArray(value.item_fields) ? value.item_fields.map(sanitizeCustomField) : [],
    notes: toStringArray(value.notes),
  };
}

function emptyCustomField(): CustomFieldConfig {
  return {
    key: '',
    label: '',
    type: 'short_text',
    description: '',
    required: false,
    options: [],
    fields: [],
    item_fields: [],
    notes: [],
  };
}

function StringListEditor({
  label,
  values,
  addLabel,
  onChange,
}: {
  label: string;
  values: string[];
  addLabel: string;
  onChange: (next: string[]) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          leadingIcon={<Plus />}
          onClick={() => onChange([...values, ''])}
        >
          {addLabel}
        </Button>
      </div>
      {values.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 px-3 py-3 text-xs text-slate-500">
          Sin elementos.
        </p>
      ) : (
        values.map((value, index) => (
          <div key={`${label}-${index}`} className="flex items-start gap-2">
            <Input
              value={value}
              onChange={(event) =>
                onChange(values.map((item, currentIndex) => (currentIndex === index ? event.target.value : item)))
              }
            />
            <IconButton
              icon={<Trash2 />}
              label="Quitar"
              variant="danger"
              onClick={() => onChange(values.filter((_, currentIndex) => currentIndex !== index))}
            />
          </div>
        ))
      )}
    </div>
  );
}

function CustomFieldBuilder({
  open,
  initial,
  onClose,
  onSubmit,
}: {
  open: boolean;
  initial: CustomFieldConfig | null;
  onClose: () => void;
  onSubmit: (field: CustomFieldConfig) => void;
}) {
  const [draft, setDraft] = useState<CustomFieldConfig>(initial ?? emptyCustomField());

  useEffect(() => {
    setDraft(initial ?? emptyCustomField());
  }, [initial, open]);

  if (!open) return null;
  const nested = draft.type === 'group' ? draft.fields : draft.type === 'group_list' ? draft.item_fields : [];

  return (
    <div className="fixed inset-0 z-[2000] flex items-center justify-center p-4">
      <button type="button" aria-label="Cerrar" className="animate-overlay absolute inset-0 bg-slate-950/60 backdrop-blur-[2px]" onClick={onClose} />
      <div className="animate-modal scrollbar-thin relative z-10 max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl">
        <h4 className="mb-3 text-base font-semibold text-slate-900">Custom field builder</h4>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Input label="Key" value={draft.key} onChange={(event) => setDraft({ ...draft, key: event.target.value })} />
          <Input label="Label" value={draft.label} onChange={(event) => setDraft({ ...draft, label: event.target.value })} />
          <Select
            label="Tipo"
            value={draft.type}
            onChange={(event) => setDraft({ ...draft, type: event.target.value as CustomFieldType })}
            options={CUSTOM_FIELD_TYPES}
          />
          <div className="flex items-end pb-1">
            <Checkbox
              label="Requerido"
              checked={draft.required}
              onChange={(event) => setDraft({ ...draft, required: event.target.checked })}
            />
          </div>
        </div>

        {draft.type === 'list' ? (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700">Opciones</p>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                leadingIcon={<Plus />}
                onClick={() => setDraft({ ...draft, options: [...draft.options, ''] })}
              >
                Agregar opcion
              </Button>
            </div>
            {draft.options.map((option, index) => (
              <div key={`option-${index}`} className="flex items-start gap-2">
                <Input
                  value={option}
                  onChange={(event) =>
                    setDraft({
                      ...draft,
                      options: draft.options.map((item, currentIndex) => (currentIndex === index ? event.target.value : item)),
                    })
                  }
                />
                <IconButton
                  icon={<Trash2 />}
                  label="Quitar"
                  variant="danger"
                  onClick={() =>
                    setDraft({
                      ...draft,
                      options: draft.options.filter((_, currentIndex) => currentIndex !== index),
                    })
                  }
                />
              </div>
            ))}
          </div>
        ) : null}

        {draft.type === 'group' || draft.type === 'group_list' ? (
          <div className="mt-4 space-y-2 rounded-xl border border-slate-200 bg-slate-50/40 p-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700">Subcampos</p>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                leadingIcon={<Plus />}
                onClick={() => {
                  const next = [...nested, emptyCustomField()];
                  setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                }}
              >
                Agregar subcampo
              </Button>
            </div>
            {nested.map((field, index) => (
              <div
                key={`nested-${index}`}
                className="grid grid-cols-1 items-end gap-2 rounded-xl border border-slate-200 bg-white p-3 md:grid-cols-[1fr_1fr_1fr_auto]"
              >
                <Input
                  placeholder="Key"
                  value={field.key}
                  onChange={(event) => {
                    const next = [...nested];
                    next[index] = { ...next[index], key: event.target.value };
                    setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                  }}
                />
                <Input
                  placeholder="Label"
                  value={field.label}
                  onChange={(event) => {
                    const next = [...nested];
                    next[index] = { ...next[index], label: event.target.value };
                    setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                  }}
                />
                <Select
                  value={field.type}
                  onChange={(event) => {
                    const next = [...nested];
                    next[index] = { ...next[index], type: event.target.value as CustomFieldType };
                    setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                  }}
                  options={CUSTOM_FIELD_TYPES}
                />
                <IconButton
                  icon={<Trash2 />}
                  label="Quitar"
                  variant="danger"
                  onClick={() => {
                    const next = nested.filter((_, currentIndex) => currentIndex !== index);
                    setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                  }}
                />
              </div>
            ))}
          </div>
        ) : null}

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={() => onSubmit(draft)}>Guardar</Button>
        </div>
      </div>
    </div>
  );
}

function MultiAppliesTo({
  value,
  userTypes,
  onChange,
}: {
  value: string[];
  userTypes: UserTypesEditable;
  onChange: (next: string[]) => void;
}) {
  const options = useMemo(
    () => [
      { value: 'all', label: 'Todos los tipos' },
      ...userTypes.types.map((type) => ({ value: type.key, label: type.label || type.key })),
    ],
    [userTypes.types],
  );

  return (
    <MultiSelect
      label="Applies to"
      options={options}
      value={value}
      onChange={onChange}
      placeholder="Selecciona tipos de usuario"
      hint="Define a quien se aplica esta entrada."
    />
  );
}

function ensureEntryId(entry: Record<string, unknown>, fieldName: 'id' | 'key' = 'id'): Record<string, unknown> {
  if (typeof entry[fieldName] === 'string' && String(entry[fieldName]).trim()) return entry;
  const generated =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${fieldName}_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  return { ...entry, [fieldName]: generated };
}

function renderCustomFields(
  section: ConfigSection,
  openBuilder: (sectionId: string, customFieldIndex: number | null, field: CustomFieldConfig | null) => void,
  updateSection: (sectionId: string, nextSection: ConfigSection) => void,
) {
  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-700">Custom fields</p>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          leadingIcon={<Plus />}
          onClick={() => openBuilder(section.id, null, null)}
        >
          Agregar custom field
        </Button>
      </div>
      {Array.isArray(section.custom_fields)
        ? section.custom_fields.map((field, index) => (
            <div
              key={`${section.id}-custom-${index}`}
              className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm transition-colors hover:bg-slate-50/60"
            >
              <span className="font-medium text-slate-800">
                {field.label || field.key || `Custom field ${index + 1}`}
              </span>
              <div className="flex items-center gap-1.5">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => openBuilder(section.id, index, field)}
                >
                  Editar
                </Button>
                <IconButton
                  icon={<Trash2 />}
                  size="sm"
                  variant="danger"
                  label="Eliminar"
                  onClick={() =>
                    updateSection(section.id, {
                      ...section,
                      custom_fields: section.custom_fields?.filter((_, currentIndex) => currentIndex !== index) ?? [],
                    })
                  }
                />
              </div>
            </div>
          ))
        : null}
    </div>
  );
}

function renderNotes(section: ConfigSection, updateSection: (sectionId: string, nextSection: ConfigSection) => void) {
  return (
    <div className="mt-4">
      <Textarea
        label="Notes"
        value={section.notes ?? ''}
        onChange={(event) => updateSection(section.id, { ...section, notes: event.target.value })}
        rows={3}
      />
    </div>
  );
}

const SECTION_ICONS: Record<string, React.ReactNode> = {
  identity: <FileText className="h-4 w-4" />,
  tone: <Bot className="h-4 w-4" />,
  rules: <ListChecks className="h-4 w-4" />,
  objectives: <Layers className="h-4 w-4" />,
  data_collection: <Hash className="h-4 w-4" />,
};

export default function GeneralSettingsSection({
  scopeLabel,
  channelSettings,
  userTypes,
  botConfig,
  onChannelSettingsChange,
  onUserTypesChange,
  onBotConfigChange,
  onSaveChannelConfig,
  isChannelDirty,
  savingChannel,
  statusText,
}: GeneralSettingsSectionProps) {
  const [builderOpen, setBuilderOpen] = useState(false);
  const [builderInitial, setBuilderInitial] = useState<CustomFieldConfig | null>(null);
  const [builderSectionId, setBuilderSectionId] = useState('');
  const [builderCustomFieldIndex, setBuilderCustomFieldIndex] = useState<number | null>(null);

  const orderedSections = useMemo(
    () => [...botConfig.sections].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0)),
    [botConfig.sections],
  );

  const updateSection = (sectionId: string, nextSection: ConfigSection) => {
    onBotConfigChange({
      ...botConfig,
      sections: botConfig.sections.map((section) => (section.id === sectionId ? nextSection : section)),
    });
  };

  const openBuilder = (sectionId: string, customFieldIndex: number | null, field: CustomFieldConfig | null) => {
    setBuilderSectionId(sectionId);
    setBuilderCustomFieldIndex(customFieldIndex);
    setBuilderInitial(field);
    setBuilderOpen(true);
  };

  const saveBuilder = (field: CustomFieldConfig) => {
    const section = botConfig.sections.find((item) => item.id === builderSectionId);
    if (!section) return;
    const list = Array.isArray(section.custom_fields) ? [...section.custom_fields] : [];
    if (builderCustomFieldIndex === null) list.push(field);
    else list[builderCustomFieldIndex] = field;
    updateSection(section.id, { ...section, custom_fields: list });
    setBuilderOpen(false);
    setBuilderInitial(null);
  };

  return (
    <section className="space-y-6">
      <Card
        icon={<Settings2 className="h-5 w-5" />}
        title="Operacion por canal"
        description={`Alcance actual: ${scopeLabel}. ${statusText}`}
        actions={
          <Button onClick={onSaveChannelConfig} loading={savingChannel} disabled={!isChannelDirty}>
            Guardar alcance
          </Button>
        }
      >
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input
            label="Limite de mensajes en conversacion"
            value={String(channelSettings.max_bot_messages)}
            onChange={(event) =>
              onChannelSettingsChange({ max_bot_messages: Number(event.target.value) || 0 })
            }
          />
          <Input
            label="Horas para volver automatico a AI"
            value={String(channelSettings.human_handoff_reset_hours)}
            onChange={(event) =>
              onChannelSettingsChange({
                human_handoff_reset_hours: Number(event.target.value) || 0,
              })
            }
          />
          <div className="md:col-span-2">
            <Textarea
              label="Mensaje automatico de limite"
              value={channelSettings.max_bot_messages_message}
              onChange={(event) =>
                onChannelSettingsChange({ max_bot_messages_message: event.target.value })
              }
              rows={3}
            />
          </div>
          <div className="md:col-span-2">
            <Textarea
              label="Mensaje automatico de media no soportada"
              value={channelSettings.unsupported_content_message}
              onChange={(event) =>
                onChannelSettingsChange({ unsupported_content_message: event.target.value })
              }
              rows={3}
            />
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50/40 p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-slate-900">Tipos de usuario</h3>
            <Button
              variant="secondary"
              size="sm"
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
          </div>
          <div className="space-y-3">
            {userTypes.types.map((userType, index) => (
              <div
                key={userType.key || `user-type-${index}`}
                className="grid grid-cols-1 items-end gap-3 rounded-xl border border-slate-200 bg-white p-3 md:grid-cols-[1fr_140px_160px_auto]"
              >
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
                  <div className="flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-2 py-1 transition-colors hover:border-slate-400">
                    <input
                      type="color"
                      value={userType.color}
                      onChange={(event) => {
                        const next = [...userTypes.types];
                        next[index] = { ...next[index], color: event.target.value };
                        onUserTypesChange({ ...userTypes, types: next });
                      }}
                      className="h-7 w-7 cursor-pointer rounded border-0 bg-transparent"
                    />
                    <code className="font-mono text-xs text-slate-600">{userType.color}</code>
                  </div>
                </div>
                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-slate-700">Default</label>
                  <Switch
                    layout="inline"
                    label={userType.is_default ? 'Seleccionado' : 'Marcar default'}
                    checked={userType.is_default}
                    onChange={() => {
                      const next = userTypes.types.map((item, currentIndex) => ({
                        ...item,
                        is_default: currentIndex === index,
                      }));
                      onUserTypesChange({
                        ...userTypes,
                        types: next,
                        default_type: next[index].key,
                      });
                    }}
                  />
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
        </div>
      </Card>

      <div className="space-y-4">
        <h3 className="text-base font-semibold text-slate-800">Configuracion del bot</h3>
        {orderedSections.map((section) => {
          const fields = toObject(section.fields);
          const entries = toEntries(section.entries);
          const icon = SECTION_ICONS[section.id] ?? <Bot className="h-4 w-4" />;

          if (section.id === 'identity') {
            const socials = Array.isArray(fields.socials) ? fields.socials.map((item) => toObject(item)) : [];
            return (
              <Card key={section.id} icon={icon} title="Identity">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <Input
                    label="Bot name"
                    value={typeof fields.bot_name === 'string' ? fields.bot_name : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, bot_name: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Company name"
                    value={typeof fields.company_name === 'string' ? fields.company_name : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, company_name: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Industry"
                    value={typeof fields.industry === 'string' ? fields.industry : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, industry: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Language"
                    value={typeof fields.language === 'string' ? fields.language : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, language: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Location"
                    value={typeof fields.location === 'string' ? fields.location : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, location: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Website"
                    value={typeof fields.website === 'string' ? fields.website : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, website: event.target.value },
                      })
                    }
                  />
                  <div className="md:col-span-2">
                    <Textarea
                      label="Description"
                      value={typeof fields.description === 'string' ? fields.description : ''}
                      onChange={(event) =>
                        updateSection(section.id, {
                          ...section,
                          fields: { ...fields, description: event.target.value },
                        })
                      }
                      rows={3}
                    />
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-700">Socials</p>
                    <Button
                      type="button"
                      variant="secondary"
                      size="sm"
                      leadingIcon={<Plus />}
                      onClick={() =>
                        updateSection(section.id, {
                          ...section,
                          fields: { ...fields, socials: [...socials, { network: '', url: '' }] },
                        })
                      }
                    >
                      Agregar social
                    </Button>
                  </div>
                  {socials.map((social, index) => (
                    <div
                      key={`social-${index}`}
                      className="grid grid-cols-1 items-start gap-2 rounded-xl border border-slate-200 bg-white p-3 md:grid-cols-[1fr_2fr_auto]"
                    >
                      <Input
                        value={typeof social.network === 'string' ? social.network : ''}
                        placeholder="Network"
                        onChange={(event) =>
                          updateSection(section.id, {
                            ...section,
                            fields: {
                              ...fields,
                              socials: socials.map((item, currentIndex) =>
                                currentIndex === index ? { ...item, network: event.target.value } : item,
                              ),
                            },
                          })
                        }
                      />
                      <Input
                        value={typeof social.url === 'string' ? social.url : ''}
                        placeholder="https://"
                        onChange={(event) =>
                          updateSection(section.id, {
                            ...section,
                            fields: {
                              ...fields,
                              socials: socials.map((item, currentIndex) =>
                                currentIndex === index ? { ...item, url: event.target.value } : item,
                              ),
                            },
                          })
                        }
                      />
                      <IconButton
                        icon={<Trash2 />}
                        label="Quitar"
                        variant="danger"
                        onClick={() =>
                          updateSection(section.id, {
                            ...section,
                            fields: {
                              ...fields,
                              socials: socials.filter((_, currentIndex) => currentIndex !== index),
                            },
                          })
                        }
                      />
                    </div>
                  ))}
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </Card>
            );
          }

          if (section.id === 'tone') {
            return (
              <Card key={section.id} icon={icon} title="Tone">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <Input
                    label="Tone"
                    value={typeof fields.tone === 'string' ? fields.tone : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, tone: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Formality"
                    value={typeof fields.formality === 'string' ? fields.formality : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, formality: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Response length"
                    value={typeof fields.response_length === 'string' ? fields.response_length : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, response_length: event.target.value },
                      })
                    }
                  />
                  <Input
                    label="Emoji usage"
                    value={typeof fields.emoji_usage === 'string' ? fields.emoji_usage : ''}
                    onChange={(event) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, emoji_usage: event.target.value },
                      })
                    }
                  />
                </div>
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  <StringListEditor
                    label="Style rules"
                    values={toStringArray(fields.style_rules)}
                    addLabel="Agregar item"
                    onChange={(next) =>
                      updateSection(section.id, { ...section, fields: { ...fields, style_rules: next } })
                    }
                  />
                  <StringListEditor
                    label="Conversation examples"
                    values={toStringArray(fields.conversation_examples)}
                    addLabel="Agregar item"
                    onChange={(next) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, conversation_examples: next },
                      })
                    }
                  />
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </Card>
            );
          }

          if (section.id === 'rules') {
            return (
              <Card key={section.id} icon={icon} title="Rules">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <StringListEditor
                    label="Global rules"
                    values={toStringArray(fields.global_rules)}
                    addLabel="Agregar item"
                    onChange={(next) =>
                      updateSection(section.id, { ...section, fields: { ...fields, global_rules: next } })
                    }
                  />
                  <StringListEditor
                    label="Business rules"
                    values={toStringArray(fields.business_rules)}
                    addLabel="Agregar item"
                    onChange={(next) =>
                      updateSection(section.id, {
                        ...section,
                        fields: { ...fields, business_rules: next },
                      })
                    }
                  />
                  <StringListEditor
                    label="Safety rules"
                    values={toStringArray(fields.safety_rules)}
                    addLabel="Agregar item"
                    onChange={(next) =>
                      updateSection(section.id, { ...section, fields: { ...fields, safety_rules: next } })
                    }
                  />
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </Card>
            );
          }

          if (section.id === 'objectives') {
            return (
              <Card
                key={section.id}
                icon={icon}
                title="Objectives"
                actions={
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    leadingIcon={<Plus />}
                    onClick={() =>
                      updateSection(section.id, {
                        ...section,
                        entries: [...entries, ensureEntryId({ ...OBJECTIVES_ENTRY_TEMPLATE })],
                      })
                    }
                  >
                    Agregar objective
                  </Button>
                }
              >
                <div className="space-y-3">
                  {entries.map((entry, entryIndex) => {
                    const current = ensureEntryId(entry);
                    const replaceEntry = (next: Record<string, unknown>) =>
                      updateSection(section.id, {
                        ...section,
                        entries: entries.map((item, currentIndex) => (currentIndex === entryIndex ? next : item)),
                      });
                    return (
                      <div
                        key={`objective-${entryIndex}`}
                        className="space-y-3 rounded-xl border border-slate-200 bg-white p-4"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-800">
                            {typeof current.name === 'string' && current.name
                              ? current.name
                              : `Objective ${entryIndex + 1}`}
                          </p>
                          <Switch
                            layout="inline"
                            label="Enabled"
                            size="sm"
                            checked={typeof current.enabled === 'boolean' ? current.enabled : true}
                            onChange={(event) => replaceEntry({ ...current, enabled: event.target.checked })}
                          />
                        </div>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <Input
                            label="Name"
                            value={typeof current.name === 'string' ? current.name : ''}
                            onChange={(event) => replaceEntry({ ...current, name: event.target.value })}
                          />
                          <MultiAppliesTo
                            value={toStringArray(current.applies_to)}
                            userTypes={userTypes}
                            onChange={(next) => replaceEntry({ ...current, applies_to: next })}
                          />
                        </div>
                        <Textarea
                          label="Objective"
                          value={typeof current.objective === 'string' ? current.objective : ''}
                          onChange={(event) => replaceEntry({ ...current, objective: event.target.value })}
                          rows={3}
                        />
                        <Textarea
                          label="Description"
                          value={typeof current.description === 'string' ? current.description : ''}
                          onChange={(event) => replaceEntry({ ...current, description: event.target.value })}
                          rows={3}
                        />
                        <Textarea
                          label="Success condition"
                          value={typeof current.success_condition === 'string' ? current.success_condition : ''}
                          onChange={(event) => replaceEntry({ ...current, success_condition: event.target.value })}
                          rows={3}
                        />
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <StringListEditor
                            label="Guidelines"
                            values={toStringArray(current.guidelines)}
                            addLabel="Agregar item"
                            onChange={(next) => replaceEntry({ ...current, guidelines: next })}
                          />
                          <StringListEditor
                            label="Rules"
                            values={toStringArray(current.rules)}
                            addLabel="Agregar item"
                            onChange={(next) => replaceEntry({ ...current, rules: next })}
                          />
                        </div>
                        <div className="flex justify-end">
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            leadingIcon={<Trash2 />}
                            onClick={() =>
                              updateSection(section.id, {
                                ...section,
                                entries: entries.filter((_, currentIndex) => currentIndex !== entryIndex),
                              })
                            }
                          >
                            Eliminar objective
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </Card>
            );
          }

          if (section.id === 'data_collection') {
            return (
              <Card
                key={section.id}
                icon={icon}
                title="Data collection"
                actions={
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    leadingIcon={<Plus />}
                    onClick={() =>
                      updateSection(section.id, {
                        ...section,
                        entries: [...entries, ensureEntryId({ ...DATA_COLLECTION_ENTRY_TEMPLATE })],
                      })
                    }
                  >
                    Agregar entry
                  </Button>
                }
              >
                <div className="space-y-3">
                  {entries.map((entry, entryIndex) => {
                    const current = ensureEntryId(entry);
                    const dcFields = toEntries(current.fields);
                    const replaceEntry = (next: Record<string, unknown>) =>
                      updateSection(section.id, {
                        ...section,
                        entries: entries.map((item, currentIndex) => (currentIndex === entryIndex ? next : item)),
                      });
                    return (
                      <div key={`dc-entry-${entryIndex}`} className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-sm font-semibold text-slate-800">
                            {typeof current.name === 'string' && current.name ? current.name : `Entry ${entryIndex + 1}`}
                          </p>
                          <Switch
                            layout="inline"
                            label="Enabled"
                            size="sm"
                            checked={typeof current.enabled === 'boolean' ? current.enabled : true}
                            onChange={(event) => replaceEntry({ ...current, enabled: event.target.checked })}
                          />
                        </div>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <Input
                            label="Name"
                            value={typeof current.name === 'string' ? current.name : ''}
                            onChange={(event) => replaceEntry({ ...current, name: event.target.value })}
                          />
                          <Input
                            label="Display field"
                            value={typeof current.display_field === 'string' ? current.display_field : ''}
                            onChange={(event) => replaceEntry({ ...current, display_field: event.target.value })}
                          />
                          <div className="md:col-span-2">
                            <MultiAppliesTo
                              value={toStringArray(current.applies_to)}
                              userTypes={userTypes}
                              onChange={(next) => replaceEntry({ ...current, applies_to: next })}
                            />
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-medium text-slate-700">Fields</p>
                            <Button
                              type="button"
                              variant="secondary"
                              size="sm"
                              leadingIcon={<Plus />}
                              onClick={() =>
                                replaceEntry({
                                  ...current,
                                  fields: [...dcFields, ensureEntryId({ ...DATA_COLLECTION_FIELD_TEMPLATE }, 'key')],
                                })
                              }
                            >
                              Agregar field
                            </Button>
                          </div>
                          {dcFields.map((field, fieldIndex) => {
                            const fieldValue = ensureEntryId(field, 'key');
                            const replaceField = (nextField: Record<string, unknown>) =>
                              replaceEntry({
                                ...current,
                                fields: dcFields.map((item, currentIndex) =>
                                  currentIndex === fieldIndex ? nextField : item,
                                ),
                              });
                            return (
                              <div
                                key={`dc-field-${entryIndex}-${fieldIndex}`}
                                className="space-y-3 rounded-xl border border-slate-200 bg-slate-50/40 p-3"
                              >
                                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                  <Input
                                    label="Label"
                                    value={typeof fieldValue.label === 'string' ? fieldValue.label : ''}
                                    onChange={(event) => replaceField({ ...fieldValue, label: event.target.value })}
                                  />
                                  <Input
                                    label="Type"
                                    value={typeof fieldValue.type === 'string' ? fieldValue.type : ''}
                                    onChange={(event) => replaceField({ ...fieldValue, type: event.target.value })}
                                  />
                                </div>
                                <Textarea
                                  label="Description"
                                  value={typeof fieldValue.description === 'string' ? fieldValue.description : ''}
                                  onChange={(event) =>
                                    replaceField({ ...fieldValue, description: event.target.value })
                                  }
                                  rows={3}
                                />
                                <StringListEditor
                                  label="Examples"
                                  values={toStringArray(fieldValue.examples)}
                                  addLabel="Agregar item"
                                  onChange={(next) => replaceField({ ...fieldValue, examples: next })}
                                />
                                <Textarea
                                  label="Validation hint"
                                  value={
                                    typeof fieldValue.validation_hint === 'string' ? fieldValue.validation_hint : ''
                                  }
                                  onChange={(event) =>
                                    replaceField({ ...fieldValue, validation_hint: event.target.value })
                                  }
                                  rows={2}
                                />
                                <div className="flex flex-wrap items-center gap-4">
                                  <Checkbox
                                    label="Required"
                                    checked={Boolean(fieldValue.required)}
                                    onChange={(event) =>
                                      replaceField({ ...fieldValue, required: event.target.checked })
                                    }
                                  />
                                  <Checkbox
                                    label="Is name field"
                                    checked={Boolean(fieldValue.is_name_field)}
                                    onChange={(event) =>
                                      replaceField({ ...fieldValue, is_name_field: event.target.checked })
                                    }
                                  />
                                </div>
                                <div className="flex justify-end">
                                  <Button
                                    type="button"
                                    variant="destructive"
                                    size="sm"
                                    leadingIcon={<Trash2 />}
                                    onClick={() =>
                                      replaceEntry({
                                        ...current,
                                        fields: dcFields.filter((_, currentIndex) => currentIndex !== fieldIndex),
                                      })
                                    }
                                  >
                                    Eliminar field
                                  </Button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="flex justify-end">
                          <Button
                            type="button"
                            variant="destructive"
                            size="sm"
                            leadingIcon={<Trash2 />}
                            onClick={() =>
                              updateSection(section.id, {
                                ...section,
                                entries: entries.filter((_, currentIndex) => currentIndex !== entryIndex),
                              })
                            }
                          >
                            Eliminar entry
                          </Button>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </Card>
            );
          }

          return (
            <Card key={section.id} icon={icon} title={section.label || toLabel(section.id)}>
              <p className="text-sm text-slate-500">Seccion sin editor especifico.</p>
              {renderCustomFields(section, openBuilder, updateSection)}
              {renderNotes(section, updateSection)}
            </Card>
          );
        })}
      </div>

      <CustomFieldBuilder
        open={builderOpen}
        initial={builderInitial}
        onClose={() => setBuilderOpen(false)}
        onSubmit={saveBuilder}
      />
    </section>
  );
}
