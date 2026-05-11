import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { TENANT_TIMEZONE_OPTIONS } from '@/constants/timezones';
import type { TenantSettingsEditable } from '@/types/settings';

interface GeneralSettingsSectionProps {
  value: TenantSettingsEditable;
  onChange: (patch: Partial<TenantSettingsEditable>) => void;
  onSave: () => void;
  isDirty: boolean;
  saving: boolean;
}

export default function GeneralSettingsSection({ value, onChange, onSave, isDirty, saving }: GeneralSettingsSectionProps) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 md:p-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">General</h2>
          <p className="text-sm text-slate-500">Configuracion del negocio y operacion general.</p>
        </div>
        <Button onClick={onSave} disabled={!isDirty || saving}>{saving ? 'Guardando...' : 'Guardar cambios'}</Button>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <Input label="Nombre del negocio" value={value.name} onChange={(event) => onChange({ name: event.target.value })} />
        <div className="space-y-1">
          <label htmlFor="tenant-timezone-settings" className="block text-sm font-medium text-slate-700">
            Timezone
          </label>
          <select
            id="tenant-timezone-settings"
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
            value={value.timezone}
            onChange={(event) => onChange({ timezone: event.target.value })}
            required
          >
            {TENANT_TIMEZONE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
        <Input label="Industria" value={value.industry} onChange={(event) => onChange({ industry: event.target.value })} />
        <Input label="Idioma" value={value.language} onChange={(event) => onChange({ language: event.target.value })} />
        <div className="md:col-span-2">
          <Input label="URL de logo" value={value.logoUrl} onChange={(event) => onChange({ logoUrl: event.target.value })} placeholder="https://..." />
        </div>
      </div>
    </section>
  );
}
