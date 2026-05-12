import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import type { BotConfigEditable, ConfigSection, CustomFieldConfig, CustomFieldType } from '@/types/channelConfig';
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
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function toEntries(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null && !Array.isArray(item)) : [];
}

function sanitizeCustomField(raw: unknown): CustomFieldConfig {
  const value = toObject(raw);
  return {
    key: typeof value.key === 'string' ? value.key : '',
    label: typeof value.label === 'string' ? value.label : '',
    type: value.type === 'short_text' || value.type === 'long_text' || value.type === 'list' || value.type === 'group' || value.type === 'group_list'
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
  return { key: '', label: '', type: 'short_text', description: '', required: false, options: [], fields: [], item_fields: [], notes: [] };
}

function StringListEditor({ label, values, addLabel, onChange }: { label: string; values: string[]; addLabel: string; onChange: (next: string[]) => void }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        <Button variant="secondary" onClick={() => onChange([...values, ''])}>{addLabel}</Button>
      </div>
      {values.map((value, index) => (
        <div key={`${label}-${index}`} className="flex gap-2">
          <input value={value} onChange={(event) => onChange(values.map((item, currentIndex) => currentIndex === index ? event.target.value : item))} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900" />
          <Button variant="danger" onClick={() => onChange(values.filter((_, currentIndex) => currentIndex !== index))}>Eliminar</Button>
        </div>
      ))}
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-xl bg-white p-4">
        <h4 className="mb-3 text-base font-semibold text-slate-900">Custom field builder</h4>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Input label="Key" value={draft.key} onChange={(event) => setDraft({ ...draft, key: event.target.value })} />
          <Input label="Label" value={draft.label} onChange={(event) => setDraft({ ...draft, label: event.target.value })} />
          <div className="space-y-1">
            <label className="block text-sm font-medium text-slate-700">Tipo</label>
            <select className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" value={draft.type} onChange={(event) => setDraft({ ...draft, type: event.target.value as CustomFieldType })}>
              {CUSTOM_FIELD_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
            </select>
          </div>
          <label className="flex items-end gap-2 text-sm text-slate-700"><input type="checkbox" checked={draft.required} onChange={(event) => setDraft({ ...draft, required: event.target.checked })} />Requerido</label>
        </div>

        {draft.type === 'list' ? (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-700">Opciones</p><Button variant="secondary" onClick={() => setDraft({ ...draft, options: [...draft.options, ''] })}>Agregar opcion</Button></div>
            {draft.options.map((option, index) => (
              <div key={`option-${index}`} className="flex gap-2">
                <input className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" value={option} onChange={(event) => setDraft({ ...draft, options: draft.options.map((item, currentIndex) => currentIndex === index ? event.target.value : item) })} />
                <Button variant="danger" onClick={() => setDraft({ ...draft, options: draft.options.filter((_, currentIndex) => currentIndex !== index) })}>Eliminar</Button>
              </div>
            ))}
          </div>
        ) : null}

        {(draft.type === 'group' || draft.type === 'group_list') ? (
          <div className="mt-4 space-y-2 rounded-lg border border-slate-200 p-3">
            <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-700">Subcampos</p><Button variant="secondary" onClick={() => {
              const next = [...nested, emptyCustomField()];
              setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
            }}>Agregar subcampo</Button></div>
            {nested.map((field, index) => (
              <div key={`nested-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-2 md:grid-cols-[1fr_1fr_1fr_auto]">
                <input className="rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="Key" value={field.key} onChange={(event) => {
                  const next = [...nested];
                  next[index] = { ...next[index], key: event.target.value };
                  setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                }} />
                <input className="rounded-lg border border-slate-300 px-3 py-2 text-sm" placeholder="Label" value={field.label} onChange={(event) => {
                  const next = [...nested];
                  next[index] = { ...next[index], label: event.target.value };
                  setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                }} />
                <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm" value={field.type} onChange={(event) => {
                  const next = [...nested];
                  next[index] = { ...next[index], type: event.target.value as CustomFieldType };
                  setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                }}>
                  {CUSTOM_FIELD_TYPES.map((type) => <option key={type.value} value={type.value}>{type.label}</option>)}
                </select>
                <Button variant="danger" onClick={() => {
                  const next = nested.filter((_, currentIndex) => currentIndex !== index);
                  setDraft(draft.type === 'group' ? { ...draft, fields: next } : { ...draft, item_fields: next });
                }}>Eliminar</Button>
              </div>
            ))}
          </div>
        ) : null}

        <div className="mt-4 flex justify-end gap-2">
          <Button variant="secondary" onClick={onClose}>Cancelar</Button>
          <Button onClick={() => onSubmit(draft)}>Guardar</Button>
        </div>
      </div>
    </div>
  );
}

function MultiAppliesTo({ value, userTypes, onChange }: { value: string[]; userTypes: UserTypesEditable; onChange: (next: string[]) => void }) {
  const options = [{ key: 'all', label: 'all' }, ...userTypes.types.map((type) => ({ key: type.key, label: type.label || type.key }))];
  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-slate-700">Applies to</label>
      <select
        multiple
        value={value}
        onChange={(event) => onChange(Array.from(event.target.selectedOptions).map((item) => item.value))}
        className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900"
      >
        {options.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}
      </select>
      <p className="text-xs text-slate-500">Mantener presionada Ctrl/Cmd para seleccionar multiples valores.</p>
    </div>
  );
}

function ensureEntryId(entry: Record<string, unknown>, fieldName: 'id' | 'key' = 'id'): Record<string, unknown> {
  if (typeof entry[fieldName] === 'string' && String(entry[fieldName]).trim()) return entry;
  const generated = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
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
      <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-700">Custom fields</p><Button variant="secondary" onClick={() => openBuilder(section.id, null, null)}>Agregar custom field</Button></div>
      {Array.isArray(section.custom_fields) ? section.custom_fields.map((field, index) => (
        <div key={`${section.id}-custom-${index}`} className="flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm"><span>{field.label || field.key || `Custom field ${index + 1}`}</span><div className="flex gap-2"><Button variant="secondary" onClick={() => openBuilder(section.id, index, field)}>Editar</Button><Button variant="danger" onClick={() => updateSection(section.id, { ...section, custom_fields: section.custom_fields?.filter((_, currentIndex) => currentIndex !== index) ?? [] })}>Eliminar</Button></div></div>
      )) : null}
    </div>
  );
}

function renderNotes(section: ConfigSection, updateSection: (sectionId: string, nextSection: ConfigSection) => void) {
  return (
    <div className="mt-4 space-y-1.5">
      <label className="block text-sm font-medium text-slate-700">Notes</label>
      <textarea value={section.notes ?? ''} onChange={(event) => updateSection(section.id, { ...section, notes: event.target.value })} className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
    </div>
  );
}

export default function GeneralSettingsSection({
  scopeLabel, channelSettings, userTypes, botConfig, onChannelSettingsChange, onUserTypesChange, onBotConfigChange,
  onSaveChannelConfig, isChannelDirty, savingChannel, statusText,
}: GeneralSettingsSectionProps) {
  const [builderOpen, setBuilderOpen] = useState(false);
  const [builderInitial, setBuilderInitial] = useState<CustomFieldConfig | null>(null);
  const [builderSectionId, setBuilderSectionId] = useState('');
  const [builderCustomFieldIndex, setBuilderCustomFieldIndex] = useState<number | null>(null);

  const orderedSections = useMemo(() => [...botConfig.sections].sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0)), [botConfig.sections]);

  const updateSection = (sectionId: string, nextSection: ConfigSection) => {
    onBotConfigChange({
      ...botConfig,
      sections: botConfig.sections.map((section) => section.id === sectionId ? nextSection : section),
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
      <div className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div><h3 className="text-base font-semibold text-slate-800">Operacion por canal</h3><p className="text-sm text-slate-500">Alcance actual: {scopeLabel}. {statusText}</p></div>
          <Button onClick={onSaveChannelConfig} disabled={!isChannelDirty || savingChannel}>{savingChannel ? 'Guardando...' : 'Guardar alcance'}</Button>
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <Input label="Limite de mensajes en conversacion" value={String(channelSettings.max_bot_messages)} onChange={(event) => onChannelSettingsChange({ max_bot_messages: Number(event.target.value) || 0 })} />
          <Input label="Horas para volver automatico a AI" value={String(channelSettings.human_handoff_reset_hours)} onChange={(event) => onChannelSettingsChange({ human_handoff_reset_hours: Number(event.target.value) || 0 })} />
          <div className="space-y-1.5 md:col-span-2"><label className="block text-sm font-medium text-slate-700">Mensaje automatico de limite</label><textarea value={channelSettings.max_bot_messages_message} onChange={(event) => onChannelSettingsChange({ max_bot_messages_message: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
          <div className="space-y-1.5 md:col-span-2"><label className="block text-sm font-medium text-slate-700">Mensaje automatico de media no soportada</label><textarea value={channelSettings.unsupported_content_message} onChange={(event) => onChannelSettingsChange({ unsupported_content_message: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
        </div>

        <div className="mt-6 rounded-xl border border-slate-100 p-4">
          <div className="mb-3 flex items-center justify-between"><h3 className="text-base font-semibold text-slate-800">Tipos de usuario</h3><Button variant="secondary" onClick={() => onUserTypesChange({ ...userTypes, types: [...userTypes.types, { key: `type_${userTypes.types.length + 1}`, label: '', color: '#2563eb', is_default: false }] })}>Agregar tipo</Button></div>
          <div className="space-y-3">
            {userTypes.types.map((userType, index) => (
              <div key={userType.key || `user-type-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_140px_140px_auto]">
                <Input label="Label" value={userType.label} onChange={(event) => { const next = [...userTypes.types]; next[index] = { ...next[index], label: event.target.value }; onUserTypesChange({ ...userTypes, types: next }); }} />
                <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Color</label><input type="color" value={userType.color} onChange={(event) => { const next = [...userTypes.types]; next[index] = { ...next[index], color: event.target.value }; onUserTypesChange({ ...userTypes, types: next }); }} className="h-10 w-full rounded-lg border border-slate-300" /></div>
                <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Default</label><Button variant={userType.is_default ? 'primary' : 'secondary'} onClick={() => { const next = userTypes.types.map((item, currentIndex) => ({ ...item, is_default: currentIndex === index })); onUserTypesChange({ ...userTypes, types: next, default_type: next[index].key }); }}>{userType.is_default ? 'Seleccionado' : 'Seleccionar'}</Button></div>
                <div className="flex items-end"><Button variant="danger" onClick={() => onUserTypesChange({ ...userTypes, types: userTypes.types.filter((_, currentIndex) => currentIndex !== index) })}>Eliminar</Button></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="text-base font-semibold text-slate-800">Configuracion del bot</h3>
        {orderedSections.map((section) => {
          const fields = toObject(section.fields);
          const entries = toEntries(section.entries);

          if (section.id === 'identity') {
            const socials = Array.isArray(fields.socials) ? fields.socials.map((item) => toObject(item)) : [];
            return (
              <section key={section.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-3 text-sm font-semibold text-slate-900">Identity</h4>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <Input label="Bot name" value={typeof fields.bot_name === 'string' ? fields.bot_name : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, bot_name: event.target.value } })} />
                  <Input label="Company name" value={typeof fields.company_name === 'string' ? fields.company_name : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, company_name: event.target.value } })} />
                  <Input label="Industry" value={typeof fields.industry === 'string' ? fields.industry : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, industry: event.target.value } })} />
                  <Input label="Language" value={typeof fields.language === 'string' ? fields.language : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, language: event.target.value } })} />
                  <Input label="Location" value={typeof fields.location === 'string' ? fields.location : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, location: event.target.value } })} />
                  <Input label="Website" value={typeof fields.website === 'string' ? fields.website : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, website: event.target.value } })} />
                  <div className="space-y-1.5 md:col-span-2"><label className="block text-sm font-medium text-slate-700">Description</label><textarea value={typeof fields.description === 'string' ? fields.description : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, description: event.target.value } })} className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-700">Socials</p><Button variant="secondary" onClick={() => updateSection(section.id, { ...section, fields: { ...fields, socials: [...socials, { network: '', url: '' }] } })}>Agregar social</Button></div>
                  {socials.map((social, index) => (
                    <div key={`social-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_2fr_auto]">
                      <input value={typeof social.network === 'string' ? social.network : ''} placeholder="Network" onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, socials: socials.map((item, currentIndex) => currentIndex === index ? { ...item, network: event.target.value } : item) } })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                      <input value={typeof social.url === 'string' ? social.url : ''} placeholder="https://" onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, socials: socials.map((item, currentIndex) => currentIndex === index ? { ...item, url: event.target.value } : item) } })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                      <Button variant="danger" onClick={() => updateSection(section.id, { ...section, fields: { ...fields, socials: socials.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button>
                    </div>
                  ))}
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </section>
            );
          }

          if (section.id === 'tone') {
            return (
              <section key={section.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-3 text-sm font-semibold text-slate-900">Tone</h4>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <Input label="Tone" value={typeof fields.tone === 'string' ? fields.tone : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, tone: event.target.value } })} />
                  <Input label="Formality" value={typeof fields.formality === 'string' ? fields.formality : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, formality: event.target.value } })} />
                  <Input label="Response length" value={typeof fields.response_length === 'string' ? fields.response_length : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, response_length: event.target.value } })} />
                  <Input label="Emoji usage" value={typeof fields.emoji_usage === 'string' ? fields.emoji_usage : ''} onChange={(event) => updateSection(section.id, { ...section, fields: { ...fields, emoji_usage: event.target.value } })} />
                </div>
                <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                  <StringListEditor label="Style rules" values={toStringArray(fields.style_rules)} addLabel="Agregar item" onChange={(next) => updateSection(section.id, { ...section, fields: { ...fields, style_rules: next } })} />
                  <StringListEditor label="Conversation examples" values={toStringArray(fields.conversation_examples)} addLabel="Agregar item" onChange={(next) => updateSection(section.id, { ...section, fields: { ...fields, conversation_examples: next } })} />
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </section>
            );
          }

          if (section.id === 'rules') {
            return (
              <section key={section.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <h4 className="mb-3 text-sm font-semibold text-slate-900">Rules</h4>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <StringListEditor label="Global rules" values={toStringArray(fields.global_rules)} addLabel="Agregar item" onChange={(next) => updateSection(section.id, { ...section, fields: { ...fields, global_rules: next } })} />
                  <StringListEditor label="Business rules" values={toStringArray(fields.business_rules)} addLabel="Agregar item" onChange={(next) => updateSection(section.id, { ...section, fields: { ...fields, business_rules: next } })} />
                  <StringListEditor label="Safety rules" values={toStringArray(fields.safety_rules)} addLabel="Agregar item" onChange={(next) => updateSection(section.id, { ...section, fields: { ...fields, safety_rules: next } })} />
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </section>
            );
          }

          if (section.id === 'objectives') {
            return (
              <section key={section.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="mb-3 flex items-center justify-between"><h4 className="text-sm font-semibold text-slate-900">Objectives</h4><Button variant="secondary" onClick={() => updateSection(section.id, { ...section, entries: [...entries, ensureEntryId({ ...OBJECTIVES_ENTRY_TEMPLATE })] })}>Agregar objective</Button></div>
                <div className="space-y-3">
                  {entries.map((entry, entryIndex) => {
                    const current = ensureEntryId(entry);
                    const replaceEntry = (next: Record<string, unknown>) => updateSection(section.id, { ...section, entries: entries.map((item, currentIndex) => currentIndex === entryIndex ? next : item) });
                    return (
                      <div key={`objective-${entryIndex}`} className="space-y-3 rounded-lg border border-slate-200 p-3">
                        <div className="flex items-center justify-between"><p className="text-sm font-semibold text-slate-800">{typeof current.name === 'string' && current.name ? current.name : `Objective ${entryIndex + 1}`}</p><label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={typeof current.enabled === 'boolean' ? current.enabled : true} onChange={(event) => replaceEntry({ ...current, enabled: event.target.checked })} />Enabled</label></div>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <Input label="Name" value={typeof current.name === 'string' ? current.name : ''} onChange={(event) => replaceEntry({ ...current, name: event.target.value })} />
                          <MultiAppliesTo value={toStringArray(current.applies_to)} userTypes={userTypes} onChange={(next) => replaceEntry({ ...current, applies_to: next })} />
                        </div>
                        <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Objective</label><textarea value={typeof current.objective === 'string' ? current.objective : ''} onChange={(event) => replaceEntry({ ...current, objective: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
                        <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Description</label><textarea value={typeof current.description === 'string' ? current.description : ''} onChange={(event) => replaceEntry({ ...current, description: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
                        <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Success condition</label><textarea value={typeof current.success_condition === 'string' ? current.success_condition : ''} onChange={(event) => replaceEntry({ ...current, success_condition: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <StringListEditor label="Guidelines" values={toStringArray(current.guidelines)} addLabel="Agregar item" onChange={(next) => replaceEntry({ ...current, guidelines: next })} />
                          <StringListEditor label="Rules" values={toStringArray(current.rules)} addLabel="Agregar item" onChange={(next) => replaceEntry({ ...current, rules: next })} />
                        </div>
                        <div className="flex justify-end"><Button variant="danger" onClick={() => updateSection(section.id, { ...section, entries: entries.filter((_, currentIndex) => currentIndex !== entryIndex) })}>Eliminar objective</Button></div>
                      </div>
                    );
                  })}
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </section>
            );
          }

          if (section.id === 'data_collection') {
            return (
              <section key={section.id} className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="mb-3 flex items-center justify-between"><h4 className="text-sm font-semibold text-slate-900">Data collection</h4><Button variant="secondary" onClick={() => updateSection(section.id, { ...section, entries: [...entries, ensureEntryId({ ...DATA_COLLECTION_ENTRY_TEMPLATE })] })}>Agregar entry</Button></div>
                <div className="space-y-3">
                  {entries.map((entry, entryIndex) => {
                    const current = ensureEntryId(entry);
                    const dcFields = toEntries(current.fields);
                    const replaceEntry = (next: Record<string, unknown>) => updateSection(section.id, { ...section, entries: entries.map((item, currentIndex) => currentIndex === entryIndex ? next : item) });
                    return (
                      <div key={`dc-entry-${entryIndex}`} className="space-y-3 rounded-lg border border-slate-200 p-3">
                        <div className="flex items-center justify-between"><p className="text-sm font-semibold text-slate-800">{typeof current.name === 'string' && current.name ? current.name : `Entry ${entryIndex + 1}`}</p><label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={typeof current.enabled === 'boolean' ? current.enabled : true} onChange={(event) => replaceEntry({ ...current, enabled: event.target.checked })} />Enabled</label></div>
                        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                          <Input label="Name" value={typeof current.name === 'string' ? current.name : ''} onChange={(event) => replaceEntry({ ...current, name: event.target.value })} />
                          <Input label="Display field" value={typeof current.display_field === 'string' ? current.display_field : ''} onChange={(event) => replaceEntry({ ...current, display_field: event.target.value })} />
                          <div className="md:col-span-2"><MultiAppliesTo value={toStringArray(current.applies_to)} userTypes={userTypes} onChange={(next) => replaceEntry({ ...current, applies_to: next })} /></div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between"><p className="text-sm font-medium text-slate-700">Fields</p><Button variant="secondary" onClick={() => replaceEntry({ ...current, fields: [...dcFields, ensureEntryId({ ...DATA_COLLECTION_FIELD_TEMPLATE }, 'key')] })}>Agregar field</Button></div>
                          {dcFields.map((field, fieldIndex) => {
                            const fieldValue = ensureEntryId(field, 'key');
                            const replaceField = (nextField: Record<string, unknown>) => replaceEntry({ ...current, fields: dcFields.map((item, currentIndex) => currentIndex === fieldIndex ? nextField : item) });
                            return (
                              <div key={`dc-field-${entryIndex}-${fieldIndex}`} className="space-y-3 rounded-lg border border-slate-200 p-3">
                                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                                  <Input label="Label" value={typeof fieldValue.label === 'string' ? fieldValue.label : ''} onChange={(event) => replaceField({ ...fieldValue, label: event.target.value })} />
                                  <Input label="Type" value={typeof fieldValue.type === 'string' ? fieldValue.type : ''} onChange={(event) => replaceField({ ...fieldValue, type: event.target.value })} />
                                </div>
                                <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Description</label><textarea value={typeof fieldValue.description === 'string' ? fieldValue.description : ''} onChange={(event) => replaceField({ ...fieldValue, description: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
                                <StringListEditor label="Examples" values={toStringArray(fieldValue.examples)} addLabel="Agregar item" onChange={(next) => replaceField({ ...fieldValue, examples: next })} />
                                <div className="space-y-1.5"><label className="block text-sm font-medium text-slate-700">Validation hint</label><textarea value={typeof fieldValue.validation_hint === 'string' ? fieldValue.validation_hint : ''} onChange={(event) => replaceField({ ...fieldValue, validation_hint: event.target.value })} className="min-h-20 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" /></div>
                                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                                  <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={Boolean(fieldValue.required)} onChange={(event) => replaceField({ ...fieldValue, required: event.target.checked })} />Required</label>
                                  <label className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={Boolean(fieldValue.is_name_field)} onChange={(event) => replaceField({ ...fieldValue, is_name_field: event.target.checked })} />Is name field</label>
                                </div>
                                <div className="flex justify-end"><Button variant="danger" onClick={() => replaceEntry({ ...current, fields: dcFields.filter((_, currentIndex) => currentIndex !== fieldIndex) })}>Eliminar field</Button></div>
                              </div>
                            );
                          })}
                        </div>
                        <div className="flex justify-end"><Button variant="danger" onClick={() => updateSection(section.id, { ...section, entries: entries.filter((_, currentIndex) => currentIndex !== entryIndex) })}>Eliminar entry</Button></div>
                      </div>
                    );
                  })}
                </div>
                {renderCustomFields(section, openBuilder, updateSection)}
                {renderNotes(section, updateSection)}
              </section>
            );
          }

          return (
            <section key={section.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <h4 className="mb-3 text-sm font-semibold text-slate-900">{section.label || toLabel(section.id)}</h4>
              <p className="text-sm text-slate-500">Seccion sin editor especifico.</p>
              {renderCustomFields(section, openBuilder, updateSection)}
              {renderNotes(section, updateSection)}
            </section>
          );
        })}
      </div>

      <CustomFieldBuilder open={builderOpen} initial={builderInitial} onClose={() => setBuilderOpen(false)} onSubmit={saveBuilder} />
    </section>
  );
}
