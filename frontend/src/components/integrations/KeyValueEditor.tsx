'use client';

import { Plus, Trash2 } from 'lucide-react';
import Button from '@/components/ui/Button';
import IconButton from '@/components/ui/IconButton';
import Input from '@/components/ui/Input';

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
        <Button
          type="button"
          variant="secondary"
          size="sm"
          leadingIcon={<Plus />}
          onClick={addRow}
          disabled={disabled}
        >
          Agregar
        </Button>
      </div>
      <div className="space-y-2">
        {rows.map((row, idx) => (
          <div key={`${label}-${idx}`} className="grid grid-cols-[1fr_1fr_auto] items-start gap-2">
            <Input
              value={row.key}
              onChange={(event) => updateRow(idx, 'key', event.target.value)}
              placeholder="key"
              disabled={disabled}
            />
            <Input
              value={row.value}
              onChange={(event) => updateRow(idx, 'value', event.target.value)}
              placeholder="value"
              disabled={disabled}
            />
            <IconButton
              icon={<Trash2 />}
              label="Quitar fila"
              variant="danger"
              onClick={() => removeRow(idx)}
              disabled={disabled || rows.length === 1}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
