import { AlertCircle, Play, RotateCcw } from 'lucide-react';
import { useMemo } from 'react';
import type { Message } from '@/types/chat';
import AttachmentPreview from '@/components/conversations/attachments/AttachmentPreview';

interface Props {
  message: Message;
  grouped?: boolean;
  onRetry?: (messageId: string) => void;
}

function formatTime(isoString: string): string {
  return new Date(isoString).toLocaleTimeString('es-AR', {
    hour: '2-digit',
    minute: '2-digit',
  });
}


export default function ConversationMessage({ message, grouped = false, onRetry }: Props) {
  const isInbound = message.direction === 'inbound';
  const isPending = message.status === 'pending';
  const isError = message.status === 'error';
  const attachments = useMemo(() => message.attachments ?? [], [message.attachments]);
  console.warn('[MESSAGE_RENDER]', {
    messageId: message.id,
    direction: message.direction,
    messageType: message.messageType,
    hasMedia: message.hasMedia,
    contentChars: (message.content || '').length,
    attachmentsCount: attachments.length,
  });
  console.warn('[MESSAGE_PAYLOAD]', message);

  return (
    <div className={`flex flex-col ${isInbound ? 'items-start' : 'items-end'} ${grouped ? 'mt-0.5' : 'mt-3'}`}>
      <div className="flex max-w-[70%] flex-col gap-1">
        {message.content && (
          <div
            className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed transition-opacity ${
              isPending ? 'opacity-60' : 'opacity-100'
            } ${
              isError
                ? 'rounded-tr-sm border border-red-200 bg-red-50 text-gray-900 shadow-sm'
                : isInbound
                ? 'rounded-tl-sm border border-gray-100 bg-white text-gray-900 shadow-sm'
                : 'rounded-tr-sm bg-blue-500 text-white'
            }`}
          >
            <p className="break-words whitespace-pre-wrap">{message.content}</p>
            <span
              className={`mt-1 flex select-none items-center justify-end gap-1 text-[10px] ${
                isInbound ? 'text-gray-400' : isError ? 'text-red-400' : 'text-blue-200'
              }`}
            >
              {formatTime(message.createdAt)}
              {isPending && (
                <span className="inline-block h-2.5 w-2.5 animate-spin rounded-full border border-current border-t-transparent" />
              )}
              {isError && <AlertCircle className="h-3 w-3 text-red-400" />}
            </span>
          </div>
        )}

        {attachments.map((attachment) => (
          <AttachmentPreview key={attachment.id} attachment={attachment} />
        ))}

        {isError && onRetry && (
          <button
            onClick={() => onRetry(message.id)}
            className="self-end text-[11px] text-red-500 transition-colors hover:text-red-700"
          >
            <span className="inline-flex items-center gap-1">
              <RotateCcw className="h-3 w-3" />
              Reintentar
            </span>
          </button>
        )}

        {!message.content && attachments.length === 0 && (
          <div className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-3 py-2 text-xs text-gray-500">
            <Play className="h-3.5 w-3.5" />
            Mensaje sin contenido
          </div>
        )}
      </div>
    </div>
  );
}
