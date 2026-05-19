import { useEffect, useState } from 'react';
import { AUTH_SESSION_CHANGED_EVENT, getToken } from '@/services/auth';

export function useAuthToken() {
  const [authResolved, setAuthResolved] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    const sync = () => {
      setHasToken(Boolean(getToken()));
      setAuthResolved(true);
    };
    sync();
    if (typeof window !== 'undefined') {
      window.addEventListener(AUTH_SESSION_CHANGED_EVENT, sync);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener(AUTH_SESSION_CHANGED_EVENT, sync);
      }
    };
  }, []);

  return { authResolved, hasToken };
}
