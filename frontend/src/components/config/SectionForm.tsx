import { useEffect, useMemo, useState } from 'react';
import Button from '@/components/ui/Button';
import type { BotConfigArrayItem, BotConfigObject, BotConfigSection } from '@/hooks/useBotConfig';

interface SectionFormProps {
  sectionKey: string;
  value: BotConfigSection;
  onSave: (value: BotConfigSection) => Promise<void>;
}

function toLabel(value: string): string {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function parsePrimitive(input: string): string | number | boolean | null {
  const trimmed = input.trim();

  if (trimmed === 'true') return true;
  if (trimmed === 'false') return false;
  if (trimmed === 'null') return null;

  const asNumber = Number(trimmed);
  if (trimmed !== '' && Number.isFinite(asNumber) && /^-?\d+(\.\d+)?$/.test(trimmed)) {
    return asNumber;
  }

  return input;
}

export default function SectionForm({ sectionKey, value, onSave }: SectionFormProps) {
  const [draft, setDraft] = useState<BotConfigSection>(value);
  const [newFieldKey, setNewFieldKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(value);
    setSaved(false);
    setError(null);
  }, [value]);

  const isArraySection = Array.isArray(draft);

  const isDirty = useMemo(() => JSON.stringify(draft) !== JSON.stringify(value), [draft, value]);

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSaved(false);
      await onSave(draft);
      setSaved(true);
      window.setTimeout(() => setSaved(false), 1800);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo guardar la seccion.');
    } finally {
      setSaving(false);
    }
  };

  const renderObjectEditor = () => {
    const objectValue = (draft as BotConfigObject) ?? {};

    return (
      <div className="space-y-3">
        {Object.entries(objectValue).map(([key, fieldValue]) => (
          <div key={key} className="flex items-center gap-2">
            <input
              value={key}
              disabled
              className="w-1/3 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600"
            />
            <input
              value={fieldValue === null ? 'null' : String(fieldValue)}
              onChange={(event) => {
                const nextValue = parsePrimitive(event.target.value);
                setDraft((prev) => ({ ...(prev as BotConfigObject), [key]: nextValue }));
              }}
              className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-sky-400"
            />
            <Button
              variant="ghost"
              type="button"
              onClick={() => {
                setDraft((prev) => {
                  const next = { ...(prev as BotConfigObject) };
                  delete next[key];
                  return next;
                });
              }}
            >
              Eliminar
            </Button>
          </div>
        ))}

        <div className="flex items-center gap-2">
          <input
            placeholder="Nuevo campo"
            value={newFieldKey}
            onChange={(event) => setNewFieldKey(event.target.value)}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-sky-400"
          />
          <Button
            variant="secondary"
            type="button"
            onClick={() => {
              const normalized = newFieldKey.trim();
              if (!normalized) return;

              setDraft((prev) => ({
                ...(prev as BotConfigObject),
                [normalized]: '',
              }));
              setNewFieldKey('');
            }}
          >
            Agregar campo
          </Button>
        </div>
      </div>
    );
  };

  const renderArrayEditor = () => {
    const arrayValue = (draft as BotConfigArrayItem[]) ?? [];

    return (
      <div className="space-y-3">
        {arrayValue.map((item, index) => {
          const isObjectItem = item !== null && typeof item === 'object' && !Array.isArray(item);

          return (
            <div key={`${sectionKey}-${index}`} className="rounded-lg border border-slate-200 p-3">
              {isObjectItem ? (
                <textarea
                  rows={4}
                  value={JSON.stringify(item, null, 2)}
                  onChange={(event) => {
                    try {
                      const parsed = JSON.parse(event.target.value);
                      setDraft((prev) => {
                        const next = [...(prev as BotConfigArrayItem[])];
                        next[index] = parsed;
                        return next;
                      });
                      setError(null);
                    } catch {
                      setError('JSON invalido en un elemento de la lista.');
                    }
                  }}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-sky-400"
                />
              ) : (
                <input
                  value={item === null ? 'null' : String(item)}
                  onChange={(event) => {
                    const nextValue = parsePrimitive(event.target.value);
                    setDraft((prev) => {
                      const next = [...(prev as BotConfigArrayItem[])];
                      next[index] = nextValue;
                      return next;
                    });
                  }}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-sky-400"
                />
              )}

              <div className="mt-2 flex justify-end">
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => {
                    setDraft((prev) => (prev as BotConfigArrayItem[]).filter((_, itemIndex) => itemIndex !== index));
                  }}
                >
                  Eliminar
                </Button>
              </div>
            </div>
          );
        })}

        <Button
          variant="secondary"
          type="button"
          onClick={() => {
            setDraft((prev) => [...(prev as BotConfigArrayItem[]), '']);
          }}
        >
          Agregar elemento
        </Button>
      </div>
    );
  };

  return (
    <article className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold text-slate-900">{toLabel(sectionKey)}</h2>
        <p className="mt-1 text-xs text-slate-500">
          {isArraySection ? 'Lista editable por seccion' : 'Campos dinamicos por seccion'}
        </p>
      </div>

      {isArraySection ? renderArrayEditor() : renderObjectEditor()}

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      <div className="flex items-center justify-end gap-2">
        {saved ? <span className="text-xs font-medium text-emerald-600">Guardado</span> : null}
        <Button type="button" onClick={handleSave} disabled={saving || !isDirty}>
          {saving ? 'Guardando...' : 'Guardar seccion'}
        </Button>
      </div>
    </article>
  );
}
