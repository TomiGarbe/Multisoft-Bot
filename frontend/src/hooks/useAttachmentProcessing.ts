import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
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
const POLL_INTERVAL_MS = 7000;
const RETRY_AFTER_NOT_FOUND_MS = 60000;
const TRANSCRIPTION_PENDING_TIMEOUT_MS = 120000;

const notFoundUntil = new Map<string, number>();
const pendingSince = new Map<string, number>();

function isPollingNeeded(status: Attachment['status'], snapshot: AttachmentProcessingSnapshot | null): boolean {
  if (snapshot) {
    return snapshot.status === 'pending' || snapshot.status === 'processing';
  }
  return status === 'processing';
}

function shouldFetchInitialState(attachmentId: string, status: Attachment['status']): boolean {
  if (stateCache.has(attachmentId)) return true;
  return status === 'processing';
}

function isTranscriptionCandidate(attachment: Attachment): boolean {
  if (attachment.type === 'audio' || attachment.type === 'video') return true;
  const normalizedMime = (attachment.mimeType ?? '').toLowerCase().split(';')[0].trim();
  return normalizedMime.startsWith('audio/') || normalizedMime.startsWith('video/');
}

async function fetchState(attachmentId: string): Promise<State> {
  const status = await getAttachmentProcessingStatus(attachmentId).catch((error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
      notFoundUntil.set(attachmentId, Date.now() + RETRY_AFTER_NOT_FOUND_MS);
      return null;
    }
    throw error;
  });
  if (!status) {
    return {
      loading: false,
      error: null,
      status: null,
      artifacts: [],
    };
  }
  const shouldReadArtifacts =
    status.status === 'completed' || status.status === 'partial' || status.status === 'processing';
  const artifacts = shouldReadArtifacts ? await getAttachmentArtifacts(attachmentId).catch(() => []) : [];
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
  const [hasTimedOutPending, setHasTimedOutPending] = useState(false);

  useEffect(() => {
    if (!isBackendAttachmentId) {
      setState({ loading: false, error: null, status: null, artifacts: [] });
      return;
    }
    if (!shouldFetchInitialState(attachment.id, attachment.status) && !isTranscriptionCandidate(attachment)) {
      setState(
        stateCache.get(attachment.id) ?? {
          loading: false,
          error: null,
          status: null,
          artifacts: [],
        },
      );
      return;
    }
    if (notFoundUntil.get(attachment.id) && Date.now() < (notFoundUntil.get(attachment.id) ?? 0)) {
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
  }, [attachment.id, attachment.status, isBackendAttachmentId]);

  useEffect(() => {
    const isPending = state.status?.status === 'pending' || state.status?.status === 'queued' || state.status?.status === 'processing';
    if (!isPending) {
      pendingSince.delete(attachment.id);
      return;
    }
    if (!pendingSince.has(attachment.id)) {
      pendingSince.set(attachment.id, Date.now());
    }
  }, [attachment.id, state.status?.status]);

  useEffect(() => {
    const startedAt = pendingSince.get(attachment.id);
    if (!startedAt) {
      setHasTimedOutPending(false);
      return;
    }

    const updateTimeout = () => {
      setHasTimedOutPending(Date.now() - startedAt >= TRANSCRIPTION_PENDING_TIMEOUT_MS);
    };

    updateTimeout();
    const timer = window.setInterval(updateTimeout, 1000);
    return () => window.clearInterval(timer);
  }, [attachment.id, state.status?.status]);

  useEffect(() => {
    if (!isBackendAttachmentId) return;
    if (notFoundUntil.get(attachment.id) && Date.now() < (notFoundUntil.get(attachment.id) ?? 0)) return;
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
    const extracted = state.artifacts.find((item) => item.capability === 'document_extraction' && item.payloadText);
    return { transcription, extracted };
  }, [state.artifacts]);

  return {
    loading: state.loading,
    error: state.error,
    status: state.status,
    artifacts: state.artifacts,
    hasTimedOutPending,
    ...derived,
  };
}

export function invalidateAttachmentProcessingCache(attachmentId: string): void {
  stateCache.delete(attachmentId);
  inFlight.delete(attachmentId);
  notFoundUntil.delete(attachmentId);
  pendingSince.delete(attachmentId);
}
