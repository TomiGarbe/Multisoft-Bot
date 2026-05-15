import { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, FileSearch } from 'lucide-react';
import type { Attachment } from '@/types/chat';
import { useAttachmentProcessing } from '@/hooks/useAttachmentProcessing';

export default function ProcessingArtifact({ attachment }: { attachment: Attachment }) {
  const { loading, transcription, extracted } = useAttachmentProcessing(attachment);
  const [open, setOpen] = useState(false);

  const sections = useMemo(
    () =>
      [
        transcription ? { key: 'transcription', title: 'Transcripcion disponible', text: transcription.payloadText ?? '' } : null,
        extracted ? { key: 'extracted', title: 'Texto extraido', text: extracted.payloadText ?? '' } : null,
      ].filter(Boolean) as { key: string; title: string; text: string }[],
    [transcription, extracted],
  );

  if (loading && attachment.status === 'processing') {
    return <p className="text-[11px] text-amber-700">Cargando resultados de procesamiento...</p>;
  }
  if (sections.length === 0) return null;

  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-2">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between text-left text-xs text-gray-700"
        aria-expanded={open}
        aria-label="Mostrar resultados de procesamiento"
      >
        <span className="inline-flex items-center gap-1">
          <FileSearch className="h-3.5 w-3.5" />
          {sections.map((section) => section.title).join(' - ')}
        </span>
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {open ? (
        <div className="mt-2 space-y-2">
          {sections.map((section) => (
            <div key={section.key} className="rounded-lg border border-gray-200 bg-white p-2">
              <p className="mb-1 text-[11px] font-semibold text-gray-700">{section.title}</p>
              <p className="max-h-44 overflow-y-auto whitespace-pre-wrap text-xs text-gray-700">{section.text}</p>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
