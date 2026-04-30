import { AlertCircle, Download, FileText, RotateCcw } from 'lucide-react';
import { Message } from '@/types/chat';

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

export default function ConversationMessage({
  message,
  grouped = false,
  onRetry,
}: Props) {
  const isInbound = message.direction === 'inbound';
  const isPending = message.status === 'pending';
  const isError = message.status === 'error';

  return (
    <div
      className={`flex flex-col ${isInbound ? 'items-start' : 'items-end'} ${
        grouped ? 'mt-0.5' : 'mt-3'
      }`}
    >
      <div className="max-w-[70%] flex flex-col gap-1">
        {/* Text bubble */}
        {message.content && (
          <div
            className={`px-4 py-2.5 text-sm leading-relaxed transition-opacity ${
              isPending ? 'opacity-60' : 'opacity-100'
            } ${
              isError
                ? 'bg-red-50 text-gray-900 shadow-sm border border-red-200 rounded-2xl rounded-tr-sm'
                : isInbound
                ? 'bg-white text-gray-900 shadow-sm border border-gray-100 rounded-2xl rounded-tl-sm'
                : 'bg-blue-500 text-white rounded-2xl rounded-tr-sm'
            }`}
          >
            <p className="whitespace-pre-wrap break-words">{message.content}</p>
            <span
              className={`flex items-center justify-end gap-1 text-[10px] mt-1 select-none ${
                isInbound ? 'text-gray-400' : isError ? 'text-red-400' : 'text-blue-200'
              }`}
            >
              {formatTime(message.createdAt)}
              {isPending && (
                <span className="inline-block w-2.5 h-2.5 border border-current border-t-transparent rounded-full animate-spin" />
              )}
              {isError && <AlertCircle className="w-3 h-3 text-red-400" />}
            </span>
          </div>
        )}

        {/* Retry button for failed messages */}
        {isError && onRetry && (
          <button
            onClick={() => onRetry(message.id)}
            className="self-end flex items-center gap-1 text-[11px] text-red-500 hover:text-red-700 transition-colors"
          >
            <RotateCcw className="w-3 h-3" />
            Reintentar
          </button>
        )}

        {/* Media items */}
        {message.media?.map((item, idx) => {
          if (item.type === 'image') {
            return (
              <div
                key={idx}
                className={`relative overflow-hidden rounded-2xl shadow-sm ${
                  isInbound ? 'rounded-tl-sm' : 'rounded-tr-sm'
                }`}
              >
                <img
                  src={item.url}
                  alt={item.name}
                  className="max-w-xs w-full object-cover"
                  loading="lazy"
                />
                <span className="absolute bottom-1.5 right-2 text-[10px] text-white bg-black/30 rounded px-1 select-none">
                  {formatTime(message.createdAt)}
                </span>
              </div>
            );
          }

          if (item.type === 'audio') {
            return (
              <div
                key={idx}
                className={`px-3 py-2.5 rounded-2xl shadow-sm ${
                  isInbound
                    ? 'rounded-tl-sm bg-white border border-gray-100'
                    : 'rounded-tr-sm bg-blue-500'
                }`}
              >
                <audio
                  controls
                  className="w-full h-8"
                  style={{ minWidth: '220px', maxWidth: '320px' }}
                >
                  <source src={item.url} />
                </audio>
                <span
                  className={`block text-[10px] mt-1 text-right select-none ${
                    isInbound ? 'text-gray-400' : 'text-blue-200'
                  }`}
                >
                  {formatTime(message.createdAt)}
                </span>
              </div>
            );
          }

          return (
            <a
              key={idx}
              href={item.url}
              download={item.name}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-2xl shadow-sm transition-opacity hover:opacity-80 ${
                isInbound
                  ? 'rounded-tl-sm bg-white border border-gray-100 text-gray-900'
                  : 'rounded-tr-sm bg-blue-500 text-white'
              }`}
            >
              <div
                className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  isInbound ? 'bg-gray-100' : 'bg-blue-600'
                }`}
              >
                <FileText className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{item.name}</p>
                <p
                  className={`text-[11px] ${
                    isInbound ? 'text-gray-400' : 'text-blue-200'
                  }`}
                >
                  {formatTime(message.createdAt)} · Descargar
                </p>
              </div>
              <Download className="w-4 h-4 flex-shrink-0 opacity-60" />
            </a>
          );
        })}
      </div>
    </div>
  );
}
