import { useEffect, useMemo, useRef, useState } from 'react';
import { Download, ExternalLink, RefreshCcw } from 'lucide-react';
import type { Attachment } from '@/types/chat';
import AttachmentStatusHint from './AttachmentStatusHint';
import { formatBytes, getDocumentIcon } from './attachmentUtils';

export default function DocumentAttachment({ attachment }: { attachment: Attachment }) {
  const [downloadState, setDownloadState] = useState<'idle' | 'downloading' | 'failed'>('idle');
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const downloadControllerRef = useRef<AbortController | null>(null);
  const Icon = useMemo(() => getDocumentIcon(attachment), [attachment]);

  useEffect(() => {
    return () => {
      downloadControllerRef.current?.abort();
    };
  }, []);

  const handleDownload = async () => {
    if (!attachment.downloadUrl) return;
    downloadControllerRef.current?.abort();
    const controller = new AbortController();
    downloadControllerRef.current = controller;
    setDownloadState('downloading');
    setDownloadError(null);
    try {
      const response = await fetch(attachment.downloadUrl, { signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const blob = await response.blob();
      const localUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = localUrl;
      a.download = attachment.filename ?? 'attachment';
      a.click();
      URL.revokeObjectURL(localUrl);
      setDownloadState('idle');
    } catch (error: unknown) {
      if (error instanceof DOMException && error.name === 'AbortError') return;
      setDownloadState('failed');
      setDownloadError('No se pudo descargar el archivo');
    } finally {
      downloadControllerRef.current = null;
    }
  };

  if (!attachment.downloadUrl && !attachment.streamUrl) return <AttachmentStatusHint attachment={attachment} />;

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-3 shadow-sm">
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-gray-100 text-gray-700">
          <Icon className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-gray-900">{attachment.filename ?? 'Archivo'}</p>
          <p className="text-[11px] text-gray-500">{formatBytes(attachment.sizeBytes ?? 0)}</p>
            {downloadState === 'downloading' ? <p className="text-[11px] text-blue-600">Descargando...</p> : null}
            {downloadError ? <p className="text-[11px] text-red-600">{downloadError}</p> : null}
        </div>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={() => void handleDownload()}
          disabled={downloadState === 'downloading'}
          className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50 disabled:opacity-60"
          aria-label="Descargar archivo"
        >
          <Download className="h-3.5 w-3.5" />
          Descargar
        </button>
        {attachment.streamUrl ? (
          <a
            href={attachment.streamUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-lg border border-gray-300 px-2 py-1 text-xs text-gray-700 hover:bg-gray-50"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Abrir
          </a>
        ) : null}
        {downloadState === 'failed' ? (
          <button
            type="button"
            onClick={() => void handleDownload()}
            className="inline-flex items-center gap-1 rounded-lg border border-red-300 px-2 py-1 text-xs text-red-700 hover:bg-red-50"
            aria-label="Reintentar descarga"
          >
            <RefreshCcw className="h-3.5 w-3.5" />
            Reintentar
          </button>
        ) : null}
      </div>
    </div>
  );
}
