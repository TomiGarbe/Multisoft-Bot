import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Plus, Trash2 } from 'lucide-react';
import Button from '@/components/ui/Button';
import IconButton from '@/components/ui/IconButton';
import Input from '@/components/ui/Input';
import Textarea from '@/components/ui/Textarea';
import type { BotConfigArrayItem, BotConfigObject, BotConfigSection } from '@/hooks/useBotConfig';

interface SectionFormProps {
  sectionKey: string;
  value: BotConfigSection;
  onSave: (value: BotConfigSection) => Promise<void>;
}

function toLabel(value: string): string {
  return value.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
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
          <div key={key} className="grid grid-cols-[140px_1fr_auto] items-start gap-2">
            <Input value={key} disabled />
            <Input
              value={fieldValue === null ? 'null' : String(fieldValue)}
              onChange={(event) => {
                const nextValue = parsePrimitive(event.target.value);
                setDraft((prev) => ({ ...(prev as BotConfigObject), [key]: nextValue }));
              }}
            />
            <IconButton
              icon={<Trash2 />}
              label="Eliminar"
              variant="danger"
              onClick={() => {
                setDraft((prev) => {
                  const next = { ...(prev as BotConfigObject) };
                  delete next[key];
                  return next;
                });
              }}
            />
          </div>
        ))}

        <div className="grid grid-cols-[1fr_auto] items-end gap-2 pt-1">
          <Input
            placeholder="Nuevo campo"
            value={newFieldKey}
            onChange={(event) => setNewFieldKey(event.target.value)}
          />
          <Button
            type="button"
            variant="secondary"
            leadingIcon={<Plus />}
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
            <div key={`${sectionKey}-${index}`} className="space-y-2 rounded-xl border border-slate-200 bg-slate-50/40 p-3">
              {isObjectItem ? (
                <Textarea
                  rows={4}
                  className="font-mono"
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
                />
              ) : (
                <Input
                  value={item === null ? 'null' : String(item)}
                  onChange={(event) => {
                    const nextValue = parsePrimitive(event.target.value);
                    setDraft((prev) => {
                      const next = [...(prev as BotConfigArrayItem[])];
                      next[index] = nextValue;
                      return next;
                    });
                  }}
                />
              )}

              <div className="flex justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  type="button"
                  leadingIcon={<Trash2 />}
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
          leadingIcon={<Plus />}
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

      <div className="flex items-center justify-end gap-3">
        {saved ? (
          <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-600">
            <CheckCircle2 className="h-3.5 w-3.5" /> Guardado
          </span>
        ) : null}
        <Button type="button" onClick={handleSave} loading={saving} disabled={!isDirty}>
          Guardar seccion
        </Button>
      </div>
    </article>
  );
}
