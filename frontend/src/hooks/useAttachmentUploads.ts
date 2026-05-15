import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';
import { resolveAttachmentTypeByFile } from '@/constants/multimedia';
import { uploadAttachmentFile } from '@/services/attachments';
import type { OutboundAttachment, PendingAttachment, UploadError, UploadProgress } from '@/types/chat';
import { validateAttachmentFile } from '@/utils/multimedia';

interface AddFilesOptions {
  replace?: boolean;
}

function toUploadError(error: unknown): UploadError {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ERR_CANCELED') return { code: 'canceled', message: 'Upload cancelado', retryable: true };
    if (error.code === 'ECONNABORTED') return { code: 'timeout', message: 'Timeout de upload', retryable: true };
    return { code: 'upload_failed', message: error.message || 'Upload fallido', retryable: true };
  }
  return { code: 'unknown', message: 'Error desconocido en upload', retryable: true };
}

export function useAttachmentUploads() {
  const [attachments, setAttachments] = useState<PendingAttachment[]>([]);
  const controllersRef = useRef<Record<string, AbortController>>({});
  const attachmentsRef = useRef<PendingAttachment[]>([]);

  useEffect(() => {
    attachmentsRef.current = attachments;
  }, [attachments]);

  useEffect(() => {
    return () => {
      Object.values(controllersRef.current).forEach((controller) => controller.abort());
      attachmentsRef.current.forEach((item) => item.previewUrl && URL.revokeObjectURL(item.previewUrl));
    };
  }, []);

  const updateAttachment = useCallback((localId: string, patch: Partial<PendingAttachment>) => {
    setAttachments((prev) => prev.map((item) => (item.localId === localId ? { ...item, ...patch } : item)));
  }, []);

  const getAttachmentById = useCallback((localId: string): PendingAttachment | undefined => {
    return attachmentsRef.current.find((item) => item.localId === localId);
  }, []);

  const detectDuration = useCallback((localId: string, file: File, mediaTag: 'audio' | 'video') => {
    const media = document.createElement(mediaTag);
    const url = URL.createObjectURL(file);
    media.preload = 'metadata';
    media.src = url;
    media.onloadedmetadata = () => {
      const durationMs = Number.isFinite(media.duration) ? Math.round(media.duration * 1000) : undefined;
      URL.revokeObjectURL(url);
      if (typeof durationMs === 'number' && durationMs > 0) updateAttachment(localId, { durationMs });
    };
    media.onerror = () => URL.revokeObjectURL(url);
  }, [updateAttachment]);

  const normalizeFiles = useCallback((files: FileList | File[]): PendingAttachment[] => {
    const list = Array.from(files);
    return list.map((file) => {
      const validationError = validateAttachmentFile(file);
      const type = resolveAttachmentTypeByFile(file);
      const localId = crypto.randomUUID();
      const previewUrl = type === 'image' ? URL.createObjectURL(file) : undefined;

      const base: PendingAttachment = {
        localId,
        file,
        type,
        previewUrl,
        uploadState: validationError ? 'failed' : 'pending',
        error: validationError ?? undefined,
      };

      if (!validationError && type === 'audio') detectDuration(localId, file, 'audio');
      if (!validationError && type === 'video') detectDuration(localId, file, 'video');
      return base;
    });
  }, [detectDuration]);

  const addFiles = useCallback((files: FileList | File[], options?: AddFilesOptions) => {
    const incoming = normalizeFiles(files);
    setAttachments((prev) => {
      if (options?.replace) {
        Object.values(controllersRef.current).forEach((controller) => controller.abort());
        controllersRef.current = {};
        prev.forEach((item) => item.previewUrl && URL.revokeObjectURL(item.previewUrl));
        return incoming;
      }
      return [...prev, ...incoming];
    });
  }, [normalizeFiles]);

  const removeAttachment = useCallback((localId: string) => {
    const controller = controllersRef.current[localId];
    if (controller) {
      controller.abort();
      delete controllersRef.current[localId];
    }
    setAttachments((prev) => {
      const target = prev.find((item) => item.localId === localId);
      if (target?.previewUrl) URL.revokeObjectURL(target.previewUrl);
      return prev.filter((item) => item.localId !== localId);
    });
  }, []);

  const cancelUpload = useCallback((localId: string) => {
    const controller = controllersRef.current[localId];
    if (controller) {
      controller.abort();
      delete controllersRef.current[localId];
    }
    updateAttachment(localId, {
      uploadState: 'canceled',
      error: { code: 'canceled', message: 'Upload cancelado', retryable: true },
    });
  }, [updateAttachment]);

  const retryUpload = useCallback((localId: string) => {
    const current = getAttachmentById(localId);
    if (!current) return;
    const validationError = validateAttachmentFile(current.file);
    updateAttachment(localId, {
      uploadState: validationError ? 'failed' : 'pending',
      progress: undefined,
      uploaded: undefined,
      error: validationError ?? undefined,
    });
  }, [getAttachmentById, updateAttachment]);

  const uploadAttachmentById = useCallback(async (localId: string): Promise<OutboundAttachment | null> => {
    const current = getAttachmentById(localId);
    if (!current) return null;
    if (current.uploadState === 'uploaded') return current.uploaded ?? null;
    if (current.uploadState === 'uploading') return null;
    if (current.uploadState === 'failed' && current.error && !current.error.retryable) return null;
    if (current.uploadState === 'canceled' || current.uploadState === 'failed' || current.uploadState === 'pending') {
      const validationError = validateAttachmentFile(current.file);
      if (validationError) {
        updateAttachment(localId, { uploadState: 'failed', error: validationError });
        return null;
      }
    }

    const controller = new AbortController();
    controllersRef.current[localId] = controller;
    updateAttachment(localId, {
      uploadState: 'uploading',
      progress: { loadedBytes: 0, totalBytes: current.file.size, percent: 0 },
      error: undefined,
    });

    try {
      const uploaded = await uploadAttachmentFile(current.file, current.type, {
        signal: controller.signal,
        onProgress: (progress: UploadProgress) => updateAttachment(localId, { progress }),
      });
      updateAttachment(localId, {
        uploadState: 'uploaded',
        uploaded,
        progress: { loadedBytes: current.file.size, totalBytes: current.file.size, percent: 100 },
      });
      return uploaded;
    } catch (error: unknown) {
      const parsed = toUploadError(error);
      updateAttachment(localId, {
        uploadState: parsed.code === 'canceled' ? 'canceled' : 'failed',
        error: parsed,
      });
      return null;
    } finally {
      delete controllersRef.current[localId];
    }
  }, [getAttachmentById, updateAttachment]);

  const uploadAllPending = useCallback(async (): Promise<{ success: boolean; outbound: OutboundAttachment[] }> => {
    const queue = attachmentsRef.current
      .filter((item) => item.uploadState === 'pending' || item.uploadState === 'failed' || item.uploadState === 'uploaded')
      .map((item) => item.localId);

    const outbound: OutboundAttachment[] = [];

    for (const localId of queue) {
      const uploaded = await uploadAttachmentById(localId);
      if (!uploaded) return { success: false, outbound: [] };
      outbound.push(uploaded);
    }

    const hasBlockingState = attachmentsRef.current.some((item) => item.uploadState === 'failed');
    if (hasBlockingState) return { success: false, outbound: [] };
    return { success: true, outbound };
  }, [uploadAttachmentById]);

  const clearAll = useCallback(() => {
    Object.values(controllersRef.current).forEach((controller) => controller.abort());
    controllersRef.current = {};
    setAttachments((prev) => {
      prev.forEach((item) => item.previewUrl && URL.revokeObjectURL(item.previewUrl));
      return [];
    });
  }, []);

  const hasUploading = useMemo(
    () => attachments.some((item) => item.uploadState === 'uploading'),
    [attachments],
  );

  return {
    attachments,
    hasUploading,
    addFiles,
    removeAttachment,
    cancelUpload,
    retryUpload,
    uploadAllPending,
    clearAll,
  };
}
