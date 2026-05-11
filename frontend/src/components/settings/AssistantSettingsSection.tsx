import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import type { BotActionConfig, BotConfigEditable, BotObjectiveConfig, DataCollectionField } from '@/types/channelConfig';

interface AssistantSettingsSectionProps {
  value: BotConfigEditable;
  onChange: (next: BotConfigEditable) => void;
}

const parseListInput = (value: string) => value.split(',').map((item) => item.trim()).filter(Boolean);

function updateStringList(list: string[], index: number, value: string) {
  const next = [...list];
  next[index] = value;
  return next;
}

export default function AssistantSettingsSection({ value, onChange }: AssistantSettingsSectionProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-slate-900">IA / Asistente</h2>
        <p className="text-sm text-slate-500">Comportamiento global del asistente con base lista para overrides por canal.</p>
      </div>
      <div className="space-y-6">
        <div className="space-y-4">
          <h3 className="text-base font-semibold text-slate-800">Identidad</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <Input label="Rol" value={value.identity.role} onChange={(event) => onChange({ ...value, identity: { ...value.identity, role: event.target.value } })} />
            <Input label="Nombre del bot" value={value.identity.bot_name} onChange={(event) => onChange({ ...value, identity: { ...value.identity, bot_name: event.target.value } })} />
            <Input label="Industria" value={value.identity.industry} onChange={(event) => onChange({ ...value, identity: { ...value.identity, industry: event.target.value } })} />
            <Input label="Idioma" value={value.identity.language} onChange={(event) => onChange({ ...value, identity: { ...value.identity, language: event.target.value } })} />
            <div className="space-y-1.5 md:col-span-2">
              <label className="block text-sm font-medium text-slate-700">Descripcion</label>
              <textarea value={value.identity.description} onChange={(event) => onChange({ ...value, identity: { ...value.identity, description: event.target.value } })} className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="text-base font-semibold text-slate-800">Tono y reglas</h3>
          <Input label="Tono" value={value.tone.tone} onChange={(event) => onChange({ ...value, tone: { ...value.tone, tone: event.target.value } })} />
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">Reglas de estilo</label>
              <Button variant="secondary" onClick={() => onChange({ ...value, tone: { ...value.tone, style_rules: [...value.tone.style_rules, ''] } })}>Agregar regla</Button>
            </div>
            {value.tone.style_rules.map((item, index) => (
              <div key={`style-rule-${index}`} className="flex gap-2">
                <input value={item} onChange={(event) => onChange({ ...value, tone: { ...value.tone, style_rules: updateStringList(value.tone.style_rules, index, event.target.value) } })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
                <Button variant="danger" onClick={() => onChange({ ...value, tone: { ...value.tone, style_rules: value.tone.style_rules.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button>
              </div>
            ))}
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-slate-700">Reglas de comportamiento</label>
              <Button variant="secondary" onClick={() => onChange({ ...value, rules: { ...value.rules, rules: [...value.rules.rules, ''] } })}>Agregar regla</Button>
            </div>
            {value.rules.rules.map((rule, index) => (
              <div key={`rule-${index}`} className="flex gap-2">
                <input value={rule} onChange={(event) => onChange({ ...value, rules: { ...value.rules, rules: updateStringList(value.rules.rules, index, event.target.value) } })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
                <Button variant="danger" onClick={() => onChange({ ...value, rules: { ...value.rules, rules: value.rules.rules.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button>
              </div>
            ))}
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium text-slate-700">Respuesta fallback</label>
            <textarea value={value.rules.fallback_message} onChange={(event) => onChange({ ...value, rules: { ...value.rules, fallback_message: event.target.value } })} className="min-h-24 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800">Herramientas habilitadas (Acciones)</h3>
            <Button variant="secondary" onClick={() => onChange({ ...value, actions: [...value.actions, { name: '', description: '' }] })}>Agregar accion</Button>
          </div>
          {value.actions.map((action: BotActionConfig, index) => (
            <div key={`action-${index}`} className="grid grid-cols-1 gap-2 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_2fr_auto]">
              <input placeholder="Nombre" value={action.name} onChange={(event) => { const nextActions = [...value.actions]; nextActions[index] = { ...nextActions[index], name: event.target.value }; onChange({ ...value, actions: nextActions }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
              <input placeholder="Descripcion" value={action.description} onChange={(event) => { const nextActions = [...value.actions]; nextActions[index] = { ...nextActions[index], description: event.target.value }; onChange({ ...value, actions: nextActions }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
              <Button variant="danger" onClick={() => onChange({ ...value, actions: value.actions.filter((_, currentIndex) => currentIndex !== index) })}>Eliminar</Button>
            </div>
          ))}
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800">Objetivos y flujo</h3>
            <Button variant="secondary" onClick={() => onChange({ ...value, objectives: [...value.objectives, { description: '', cta_message: '', applies_to: [], conversation_flow: [] }] })}>Agregar objetivo</Button>
          </div>
          {value.objectives.map((objective: BotObjectiveConfig, index) => (
            <div key={`objective-${index}`} className="space-y-3 rounded-lg border border-slate-200 p-3">
              <Input label="Descripcion" value={objective.description} onChange={(event) => { const nextObjectives = [...value.objectives]; nextObjectives[index] = { ...nextObjectives[index], description: event.target.value }; onChange({ ...value, objectives: nextObjectives }); }} />
              <Input label="Mensaje CTA" value={objective.cta_message} onChange={(event) => { const nextObjectives = [...value.objectives]; nextObjectives[index] = { ...nextObjectives[index], cta_message: event.target.value }; onChange({ ...value, objectives: nextObjectives }); }} />
              <Input label="Aplica a" value={objective.applies_to.join(', ')} onChange={(event) => { const nextObjectives = [...value.objectives]; nextObjectives[index] = { ...nextObjectives[index], applies_to: parseListInput(event.target.value) }; onChange({ ...value, objectives: nextObjectives }); }} />
              <Input label="Flujo" value={objective.conversation_flow.join(', ')} onChange={(event) => { const nextObjectives = [...value.objectives]; nextObjectives[index] = { ...nextObjectives[index], conversation_flow: parseListInput(event.target.value) }; onChange({ ...value, objectives: nextObjectives }); }} />
              <Button variant="danger" onClick={() => onChange({ ...value, objectives: value.objectives.filter((_, currentIndex) => currentIndex !== index) })}>Eliminar objetivo</Button>
            </div>
          ))}
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-slate-800">Memoria y data collection</h3>
            <Button variant="secondary" onClick={() => onChange({ ...value, data_collection: { fields: [...value.data_collection.fields, { name: '', type: '' }] } })}>Agregar campo</Button>
          </div>
          {value.data_collection.fields.map((field: DataCollectionField, index) => (
            <div key={`field-${index}`} className="grid grid-cols-1 gap-2 md:grid-cols-[1fr_220px_auto]">
              <input placeholder="Nombre" value={field.name} onChange={(event) => { const nextFields = [...value.data_collection.fields]; nextFields[index] = { ...nextFields[index], name: event.target.value }; onChange({ ...value, data_collection: { fields: nextFields } }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
              <input placeholder="Tipo" value={field.type} onChange={(event) => { const nextFields = [...value.data_collection.fields]; nextFields[index] = { ...nextFields[index], type: event.target.value }; onChange({ ...value, data_collection: { fields: nextFields } }); }} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-200" />
              <Button variant="danger" onClick={() => onChange({ ...value, data_collection: { fields: value.data_collection.fields.filter((_, currentIndex) => currentIndex !== index) } })}>Eliminar</Button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
