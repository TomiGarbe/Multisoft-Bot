import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

type RecorderStatus = 'idle' | 'requesting_permission' | 'recording' | 'ready' | 'error';

interface RecorderError {
  code:
    | 'unsupported'
    | 'permission_denied'
    | 'no_microphone'
    | 'empty_recording'
    | 'recorder_failed'
    | 'invalid_state';
  message: string;
}

interface UseAudioRecorderOptions {
  mimeType?: string;
}

const DEFAULT_MIME_CANDIDATES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus'];

function resolveMimeType(preferred?: string): string | undefined {
  if (typeof window === 'undefined' || typeof MediaRecorder === 'undefined') return undefined;
  const candidates = preferred ? [preferred, ...DEFAULT_MIME_CANDIDATES] : DEFAULT_MIME_CANDIDATES;
  return candidates.find((item) => MediaRecorder.isTypeSupported(item));
}

export function useAudioRecorder(options?: UseAudioRecorderOptions) {
  const [status, setStatus] = useState<RecorderStatus>('idle');
  const [durationMs, setDurationMs] = useState(0);
  const [error, setError] = useState<RecorderError | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const pendingStopRef = useRef<((file: File | null) => void) | null>(null);
  const previewUrlRef = useRef<string | null>(null);
  const mimeType = resolveMimeType(options?.mimeType);

  useEffect(() => {
    previewUrlRef.current = previewUrl;
  }, [previewUrl]);

  const cleanupTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  const clearPreview = useCallback(() => {
    setAudioFile(null);
    setDurationMs(0);
    if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    previewUrlRef.current = null;
    setPreviewUrl(null);
  }, []);

  const resetToIdle = useCallback(() => {
    cleanupTimer();
    cleanupStream();
    recorderRef.current = null;
    chunksRef.current = [];
    startedAtRef.current = null;
    pendingStopRef.current = null;
    setStatus('idle');
  }, [cleanupStream, cleanupTimer]);

  useEffect(() => {
    return () => {
      cleanupTimer();
      cleanupStream();
      if (previewUrlRef.current) URL.revokeObjectURL(previewUrlRef.current);
    };
  }, [cleanupStream, cleanupTimer]);

  const startRecording = useCallback(async () => {
    if (status === 'recording' || status === 'requesting_permission') return;
    if (typeof window === 'undefined' || !navigator?.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      setError({ code: 'unsupported', message: 'Tu navegador no soporta grabacion de audio' });
      setStatus('error');
      return;
    }

    clearPreview();
    setError(null);
    setStatus('requesting_permission');

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      chunksRef.current = [];
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      recorderRef.current = recorder;
      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onerror = () => {
        setError({ code: 'recorder_failed', message: 'Error grabando audio' });
        setStatus('error');
      };
      recorder.onstop = () => {
        cleanupTimer();
        cleanupStream();
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        chunksRef.current = [];
        recorderRef.current = null;

        const duration = startedAtRef.current ? Date.now() - startedAtRef.current : durationMs;
        setDurationMs(duration > 0 ? duration : durationMs);
        startedAtRef.current = null;

        if (blob.size <= 0) {
          setError({ code: 'empty_recording', message: 'La grabacion quedo vacia' });
          setStatus('error');
          pendingStopRef.current?.(null);
          pendingStopRef.current = null;
          return;
        }

        const extension = blob.type.includes('mp4') ? 'm4a' : blob.type.includes('ogg') ? 'ogg' : 'webm';
        const file = new File([blob], `audio_${Date.now()}.${extension}`, { type: blob.type || 'audio/webm' });
        const url = URL.createObjectURL(file);
        setAudioFile(file);
        setPreviewUrl(url);
        setStatus('ready');
        pendingStopRef.current?.(file);
        pendingStopRef.current = null;
      };

      recorder.start(250);
      startedAtRef.current = Date.now();
      setDurationMs(0);
      setStatus('recording');
      timerRef.current = setInterval(() => {
        if (startedAtRef.current) setDurationMs(Date.now() - startedAtRef.current);
      }, 250);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message.toLowerCase() : '';
      if (message.includes('denied') || message.includes('permission')) {
        setError({ code: 'permission_denied', message: 'Permiso de microfono denegado' });
      } else if (message.includes('notfound') || message.includes('device')) {
        setError({ code: 'no_microphone', message: 'No se encontro microfono disponible' });
      } else {
        setError({ code: 'recorder_failed', message: 'No se pudo iniciar grabacion' });
      }
      setStatus('error');
      cleanupStream();
    }
  }, [cleanupStream, cleanupTimer, clearPreview, durationMs, mimeType, status]);

  const stopRecording = useCallback(async (): Promise<File | null> => {
    if (status !== 'recording' || !recorderRef.current) {
      setError({ code: 'invalid_state', message: 'No hay grabacion activa' });
      return null;
    }
    return new Promise<File | null>((resolve) => {
      pendingStopRef.current = resolve;
      recorderRef.current?.stop();
    });
  }, [status]);

  const cancelRecording = useCallback(() => {
    setError(null);
    if (status === 'recording' && recorderRef.current) {
      pendingStopRef.current = null;
      recorderRef.current.onstop = null;
      recorderRef.current.stop();
      cleanupTimer();
      cleanupStream();
      recorderRef.current = null;
      chunksRef.current = [];
      startedAtRef.current = null;
    }
    clearPreview();
    setDurationMs(0);
    setStatus('idle');
  }, [cleanupStream, cleanupTimer, clearPreview, status]);

  const clearError = useCallback(() => {
    setError(null);
    if (status === 'error') setStatus('idle');
  }, [status]);

  const formattedDuration = useMemo(() => {
    const totalSeconds = Math.max(0, Math.floor(durationMs / 1000));
    const mm = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
    const ss = String(totalSeconds % 60).padStart(2, '0');
    return `${mm}:${ss}`;
  }, [durationMs]);

  return {
    status,
    durationMs,
    formattedDuration,
    error,
    audioFile,
    previewUrl,
    startRecording,
    stopRecording,
    cancelRecording,
    clearError,
    clearPreview,
    resetToIdle,
  };
}
