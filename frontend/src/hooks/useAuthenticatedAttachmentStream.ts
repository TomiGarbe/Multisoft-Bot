import { useEffect, useState } from 'react';
import { fetchAttachmentStreamBlob } from '@/services/attachments';

const urlCache = new Map<string, string>();
const inFlight = new Map<string, Promise<string>>();
let cleanupRegistered = false;

interface State {
  url: string | null;
  loading: boolean;
  error: boolean;
}

function isInternalAttachmentStreamUrl(candidate?: string): boolean {
  if (!candidate) return false;
  if (typeof window === 'undefined') return false;

  try {
    const direct = new URL(candidate, window.location.origin);
    const path = direct.pathname.toLowerCase();
    return path.includes('/attachments/') && (path.endsWith('/stream') || path.endsWith('/download'));
  } catch {
    return false;
  }
}

function shouldUseDirectUrl(directUrl?: string): boolean {
  if (!directUrl) return false;
  return !isInternalAttachmentStreamUrl(directUrl);
}

function registerCacheCleanupOnce(): void {
  if (cleanupRegistered || typeof window === 'undefined') return;
  cleanupRegistered = true;
  window.addEventListener('beforeunload', () => {
    for (const value of urlCache.values()) {
      URL.revokeObjectURL(value);
    }
    urlCache.clear();
    inFlight.clear();
  });
}

export function useAuthenticatedAttachmentStream(
  attachmentId: string,
  enabled: boolean,
  directUrl?: string,
): State {
  const useDirect = shouldUseDirectUrl(directUrl);

  const [state, setState] = useState<State>(() => {
    if (useDirect) {
      return {
        url: directUrl ?? null,
        loading: false,
        error: false,
      };
    }
    const cached = urlCache.get(attachmentId) ?? null;
    return {
      url: cached,
      loading: enabled && !cached,
      error: false,
    };
  });

  useEffect(() => {
    registerCacheCleanupOnce();

    if (useDirect) {
      setState({ url: directUrl ?? null, loading: false, error: false });
      return;
    }

    if (!enabled) {
      setState({ url: null, loading: false, error: false });
      return;
    }

    const cached = urlCache.get(attachmentId);
    if (cached) {
      setState({ url: cached, loading: false, error: false });
      return;
    }

    let active = true;
    const controller = new AbortController();
    setState({ url: null, loading: true, error: false });

    const running =
      inFlight.get(attachmentId) ??
      fetchAttachmentStreamBlob(attachmentId, { signal: controller.signal }).then((blob) => {
        const nextUrl = URL.createObjectURL(blob);
        urlCache.set(attachmentId, nextUrl);
        return nextUrl;
      });
    inFlight.set(attachmentId, running);

    void running
      .then((nextUrl) => {
        if (!active) return;
        setState({ url: nextUrl, loading: false, error: false });
      })
      .catch(() => {
        if (!active) return;
        setState({ url: null, loading: false, error: true });
      })
      .finally(() => {
        inFlight.delete(attachmentId);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [attachmentId, enabled, directUrl, useDirect]);

  return state;
}
