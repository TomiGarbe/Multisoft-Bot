import { useRef, useState } from 'react';
import { Paperclip, Send, Mic, X, FileText } from 'lucide-react';
import { SendPayload } from '@/types/chat';

interface Props {
  onSend: (payload: SendPayload) => void;
}

type FileMediaType = 'image' | 'audio' | 'file';

interface FilePreview {
  file: File;
  previewUrl: string | null;
  mediaType: FileMediaType;
}

function resolveMediaType(file: File): FileMediaType {
  if (file.type.startsWith('image/')) return 'image';
  if (file.type.startsWith('audio/')) return 'audio';
  return 'file';
}

export default function MessageComposer({ onSend }: Props) {
  const [text, setText] = useState('');
  const [previews, setPreviews] = useState<FilePreview[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList) return;

    const incoming: FilePreview[] = Array.from(fileList).map((file) => {
      const mediaType = resolveMediaType(file);
      const previewUrl =
        mediaType === 'image' || mediaType === 'audio'
          ? URL.createObjectURL(file)
          : null;
      return { file, previewUrl, mediaType };
    });

    setPreviews((prev) => [...prev, ...incoming]);
    e.target.value = '';
  };

  const removePreview = (index: number) => {
    setPreviews((prev) => {
      const item = prev[index];
      if (item.previewUrl) URL.revokeObjectURL(item.previewUrl);
      return prev.filter((_, i) => i !== index);
    });
  };

  const handleSend = () => {
    if (!text.trim() && previews.length === 0) return;
    onSend({ text: text.trim(), files: previews.map((p) => p.file) });
    previews.forEach((p) => {
      if (p.previewUrl) URL.revokeObjectURL(p.previewUrl);
    });
    setText('');
    setPreviews([]);
    textareaRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const hasText = text.trim().length > 0;
  const canSend = hasText || previews.length > 0;

  return (
    <div className="flex-shrink-0 border-t border-gray-200 bg-white">
      {/* File previews */}
      {previews.length > 0 && (
        <div className="px-4 pt-3 pb-1 flex gap-2 overflow-x-auto">
          {previews.map((preview, idx) => (
            <div key={idx} className="relative flex-shrink-0">
              {preview.mediaType === 'image' && preview.previewUrl ? (
                <div className="w-16 h-16 rounded-xl overflow-hidden border border-gray-200 shadow-sm">
                  <img
                    src={preview.previewUrl}
                    alt=""
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : preview.mediaType === 'audio' && preview.previewUrl ? (
                <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-3 py-2 pr-9">
                  <audio controls className="h-7" style={{ width: '180px' }}>
                    <source src={preview.previewUrl} />
                  </audio>
                </div>
              ) : (
                <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-3 py-2 pr-9">
                  <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  <span className="text-xs text-gray-700 max-w-[120px] truncate">
                    {preview.file.name}
                  </span>
                </div>
              )}

              <button
                onClick={() => removePreview(idx)}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-gray-600 hover:bg-gray-800 text-white rounded-full flex items-center justify-center transition-colors shadow-sm"
                aria-label="Quitar archivo"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input row */}
      <div className="flex items-end gap-2 px-4 py-3">
        {/* Attach */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 w-9 h-9 rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors flex items-center justify-center"
          aria-label="Adjuntar archivo"
        >
          <Paperclip className="w-5 h-5" />
        </button>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          hidden
          accept="image/*,audio/*,.pdf,.doc,.docx,.xls,.xlsx,.zip,.txt,.csv"
          onChange={handleFileChange}
        />

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder="Escribi un mensaje... (Enter para enviar)"
          className="flex-1 resize-none rounded-2xl border border-gray-200 bg-gray-50 px-4 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent focus:bg-white transition-colors overflow-y-auto"
          style={{ lineHeight: '1.5', maxHeight: '120px' }}
        />

        {/* Send */}
        <button
          onClick={handleSend}
          className="flex-shrink-0 w-9 h-9 rounded-full bg-blue-500 text-white flex items-center justify-center hover:bg-blue-600 active:bg-blue-700 transition-colors"
          aria-label={canSend ? 'Enviar' : 'Grabar audio'}
        >
          {hasText ? <Send className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
}
