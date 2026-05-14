import { useEffect, useMemo, useState } from 'react';
import { getAttachmentArtifacts, getAttachmentProcessingStatus } from '@/services/mediaProcessing';
import type { Attachment, AttachmentProcessingSnapshot, ProcessedArtifact } from '@/types/chat';

interface State {
  loading: boolean;
  error: string | null;
  status: AttachmentProcessingSnapshot | null;
  artifacts: ProcessedArtifact[];
}

const stateCache = new Map<string, State>();
const inFlight = new Map<string, Promise<State>>();
const POLL_INTERVAL_MS = 5000;

function isPollingNeeded(status: Attachment['status'], snapshot: AttachmentProcessingSnapshot | null): boolean {
  if (status === 'processing' || status === 'loading' || status === 'downloading') return true;
  if (!snapshot) return false;
  return snapshot.status === 'pending' || snapshot.status === 'queued' || snapshot.status === 'processing';
}

async function fetchState(attachmentId: string): Promise<State> {
  const [status, artifacts] = await Promise.all([
    getAttachmentProcessingStatus(attachmentId).catch(() => null),
    getAttachmentArtifacts(attachmentId).catch(() => []),
  ]);
  return {
    loading: false,
    error: null,
    status,
    artifacts,
  };
}

export function useAttachmentProcessing(attachment: Attachment) {
  const isBackendAttachmentId = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
    attachment.id,
  );
  const [state, setState] = useState<State>(() => {
    return (
      stateCache.get(attachment.id) ?? {
        loading: true,
        error: null,
        status: null,
        artifacts: [],
      }
    );
  });

  useEffect(() => {
    if (!isBackendAttachmentId) {
      setState({ loading: false, error: null, status: null, artifacts: [] });
      return;
    }
    let active = true;
    const cached = stateCache.get(attachment.id);
    if (cached) setState(cached);
    else setState({ loading: true, error: null, status: null, artifacts: [] });

    const run = async () => {
      try {
        const running = inFlight.get(attachment.id) ?? fetchState(attachment.id);
        inFlight.set(attachment.id, running);
        const next = await running;
        stateCache.set(attachment.id, next);
        if (active) setState(next);
      } catch {
        if (active) setState((prev) => ({ ...prev, loading: false, error: 'No se pudo cargar procesamiento multimedia' }));
      } finally {
        inFlight.delete(attachment.id);
      }
    };

    void run();
    return () => {
      active = false;
    };
  }, [attachment.id, isBackendAttachmentId]);

  useEffect(() => {
    if (!isBackendAttachmentId) return;
    if (!isPollingNeeded(attachment.status, state.status)) return;
    let active = true;
    let polling = false;
    const timer = window.setInterval(() => {
      if (polling) return;
      polling = true;
      const running = inFlight.get(attachment.id) ?? fetchState(attachment.id);
      inFlight.set(attachment.id, running);
      void running
        .then((next) => {
          if (!active) return;
          stateCache.set(attachment.id, next);
          setState(next);
        })
        .catch(() => {
          if (!active) return;
          setState((prev) => ({ ...prev, loading: false, error: 'No se pudo actualizar procesamiento multimedia' }));
        })
        .finally(() => {
          polling = false;
          inFlight.delete(attachment.id);
        });
    }, POLL_INTERVAL_MS);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [attachment.id, attachment.status, state.status, isBackendAttachmentId]);

  const derived = useMemo(() => {
    const transcription = state.artifacts.find((item) => item.capability === 'transcription' && item.payloadText);
    const ocr = state.artifacts.find((item) => item.capability === 'ocr' && item.payloadText);
    const extracted = state.artifacts.find((item) => item.capability === 'document_extraction' && item.payloadText);
    return { transcription, ocr, extracted };
  }, [state.artifacts]);

  return {
    loading: state.loading,
    error: state.error,
    status: state.status,
    artifacts: state.artifacts,
    ...derived,
  };
}
