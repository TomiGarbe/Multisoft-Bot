interface KeyValueEditorProps {
  label: string;
  value: Array<{ key: string; value: string }>;
  onChange: (next: Array<{ key: string; value: string }>) => void;
  disabled?: boolean;
}

export default function KeyValueEditor({ label, value, onChange, disabled }: KeyValueEditorProps) {
  const rows = value.length > 0 ? value : [{ key: '', value: '' }];

  const updateRow = (index: number, field: 'key' | 'value', fieldValue: string) => {
    const next = rows.map((row, i) => (i === index ? { ...row, [field]: fieldValue } : row));
    onChange(next);
  };

  const addRow = () => onChange([...rows, { key: '', value: '' }]);
  const removeRow = (index: number) => onChange(rows.filter((_, i) => i !== index));

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-700">{label}</p>
        <button type="button" className="text-xs font-semibold text-sky-700" onClick={addRow} disabled={disabled}>
          + Agregar
        </button>
      </div>
      <div className="space-y-2">
        {rows.map((row, idx) => (
          <div key={`${label}-${idx}`} className="grid grid-cols-[1fr_1fr_auto] gap-2">
            <input
              value={row.key}
              onChange={(event) => updateRow(idx, 'key', event.target.value)}
              placeholder="key"
              disabled={disabled}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              value={row.value}
              onChange={(event) => updateRow(idx, 'value', event.target.value)}
              placeholder="value"
              disabled={disabled}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="button"
              className="rounded-lg border border-slate-200 px-2 text-xs text-slate-600"
              onClick={() => removeRow(idx)}
              disabled={disabled || rows.length === 1}
            >
              Quitar
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
