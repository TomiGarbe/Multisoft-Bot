import { useMemo, useRef, useState } from 'react';
import { FileText, Mic, Paperclip, RotateCcw, Send, Square, X } from 'lucide-react';
import AudioRecorder from '@/components/conversations/AudioRecorder';
import { MULTIMEDIA_ACCEPT } from '@/constants/multimedia';
import { useAttachmentUploads } from '@/hooks/useAttachmentUploads';
import type { PendingAttachment, SendPayload, UploadState } from '@/types/chat';
import { formatBytes } from '@/utils/multimedia';

interface Props {
  onSend: (payload: SendPayload) => Promise<void> | void;
}

function renderUploadState(state: UploadState): string {
  if (state === 'pending') return 'Pendiente';
  if (state === 'uploading') return 'Subiendo';
  if (state === 'uploaded') return 'Subido';
  if (state === 'failed') return 'Fallido';
  return 'Cancelado';
}

function PreviewItem({
  item,
  onCancelUpload,
  onRetryUpload,
  onRemove,
}: {
  item: PendingAttachment;
  onCancelUpload: (localId: string) => void;
  onRetryUpload: (localId: string) => void;
  onRemove: (localId: string) => void;
}) {
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50 p-2">
      <div className="flex items-start gap-2">
        {item.type === 'image' && item.previewUrl ? (
          <img src={item.previewUrl} alt={item.file.name} className="h-14 w-14 rounded-lg object-cover" />
        ) : (
          <div className="flex h-14 w-14 items-center justify-center rounded-lg border border-gray-200 bg-white text-gray-500">
            <FileText className="h-5 w-5" />
          </div>
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate text-xs font-medium text-gray-800">{item.file.name}</p>
          <p className="text-[11px] text-gray-500">
            {formatBytes(item.file.size)}
            {typeof item.durationMs === 'number' ? ` - ${Math.round(item.durationMs / 1000)}s` : ''}
          </p>
          <p className="text-[11px] text-gray-600">{renderUploadState(item.uploadState)}</p>
          {item.uploadState === 'uploading' && item.progress ? (
            <div className="mt-1 h-1.5 w-full rounded bg-gray-200">
              <div className="h-1.5 rounded bg-blue-500" style={{ width: `${item.progress.percent}%` }} />
            </div>
          ) : null}
          {item.error ? <p className="mt-1 text-[11px] text-red-600">{item.error.message}</p> : null}
        </div>
        <div className="flex items-center gap-1">
          {item.uploadState === 'uploading' ? (
            <button type="button" onClick={() => onCancelUpload(item.localId)} className="rounded p-1 text-gray-500 hover:bg-gray-200" aria-label="Cancelar upload">
              <Square className="h-3.5 w-3.5" />
            </button>
          ) : null}
          {(item.uploadState === 'failed' || item.uploadState === 'canceled') && item.error?.retryable ? (
            <button type="button" onClick={() => onRetryUpload(item.localId)} className="rounded p-1 text-gray-500 hover:bg-gray-200" aria-label="Reintentar upload">
              <RotateCcw className="h-3.5 w-3.5" />
            </button>
          ) : null}
          <button type="button" onClick={() => onRemove(item.localId)} className="rounded p-1 text-gray-500 hover:bg-gray-200" aria-label="Quitar archivo">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function MessageComposer({ onSend }: Props) {
  const [text, setText] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [showRecorder, setShowRecorder] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const {
    attachments,
    hasUploading,
    addFiles,
    removeAttachment,
    cancelUpload,
    retryUpload,
    uploadAllPending,
    clearAll,
  } = useAttachmentUploads();

  const orderedAttachments = useMemo(() => attachments, [attachments]);
  const hasText = text.trim().length > 0;
  const canSend = hasText || orderedAttachments.length > 0;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    addFiles(files);
    e.target.value = '';
  };

  const handleSend = async () => {
    if (isSending) return;
    if (!text.trim() && orderedAttachments.length === 0) return;

    setIsSending(true);
    try {
      const uploadResult = await uploadAllPending();
      console.warn('[MULTIMEDIA][SEND_MESSAGE] composer_upload_result', {
        success: uploadResult.success,
        outboundCount: uploadResult.outbound.length,
      });
      if (!uploadResult.success) return;
      await onSend({ text: text.trim(), attachments: uploadResult.outbound });
      clearAll();
      setText('');
      setShowRecorder(false);
      textareaRef.current?.focus();
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  };

  const handleMicOrSend = () => {
    if (hasText || orderedAttachments.length > 0) {
      void handleSend();
      return;
    }
    setShowRecorder((prev) => !prev);
    textareaRef.current?.focus();
  };

  const handleInput = (event: React.FormEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget;
    target.style.height = '0px';
    target.style.height = `${Math.min(120, target.scrollHeight)}px`;
  };

  return (
    <div className="flex-shrink-0 bg-white">
      {showRecorder ? (
        <div className="px-4 pt-3">
          <AudioRecorder
            onRecorded={(file) => {
              addFiles([file]);
            }}
            onClose={() => setShowRecorder(false)}
          />
        </div>
      ) : null}

      {orderedAttachments.length > 0 ? (
        <div className="flex max-h-48 flex-col gap-2 overflow-y-auto px-4 pb-1 pt-3">
          {orderedAttachments.map((item) => (
            <PreviewItem
              key={item.localId}
              item={item}
              onCancelUpload={cancelUpload}
              onRetryUpload={retryUpload}
              onRemove={removeAttachment}
            />
          ))}
        </div>
      ) : null}

      <div className="flex items-end gap-2 px-4 py-3">
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
          aria-label="Adjuntar archivo"
        >
          <Paperclip className="h-5 w-5" />
        </button>

        <input ref={fileInputRef} type="file" multiple hidden accept={MULTIMEDIA_ACCEPT} onChange={handleFileChange} />

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Escribi un mensaje... (Enter para enviar)"
          className="flex-1 resize-none overflow-y-auto rounded-2xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-transparent focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          style={{ lineHeight: '1.5', maxHeight: '120px' }}
        />

        <button
          type="button"
          onClick={handleMicOrSend}
          disabled={isSending || hasUploading}
          className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full text-white transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${
            canSend ? 'bg-blue-500 hover:bg-blue-600 active:bg-blue-700' : 'bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800'
          }`}
          aria-label={canSend ? 'Enviar' : 'Grabar audio'}
        >
          {canSend ? <Send className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}
