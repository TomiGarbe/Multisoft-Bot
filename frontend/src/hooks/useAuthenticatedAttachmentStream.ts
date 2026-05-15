import { useEffect, useState } from 'react';
import { fetchAttachmentStreamBlob } from '@/services/attachments';

const urlCache = new Map<string, string>();
const inFlight = new Map<string, Promise<string>>();

interface State {
  url: string | null;
  loading: boolean;
  error: boolean;
}

export function useAuthenticatedAttachmentStream(
  attachmentId: string,
  enabled: boolean,
  directUrl?: string,
): State {
  const [state, setState] = useState<State>(() => {
    if (directUrl) {
      return {
        url: directUrl,
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
    if (directUrl) {
      setState({ url: directUrl, loading: false, error: false });
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
    setState({ url: null, loading: true, error: false });

    const running =
      inFlight.get(attachmentId) ??
      fetchAttachmentStreamBlob(attachmentId).then((blob) => {
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
    };
  }, [attachmentId, enabled, directUrl]);

  return state;
}
