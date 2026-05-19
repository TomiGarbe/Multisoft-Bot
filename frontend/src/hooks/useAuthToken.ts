import { useEffect, useState } from 'react';
import { getToken } from '@/services/auth';

export function useAuthToken() {
  const [authResolved, setAuthResolved] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    setHasToken(Boolean(getToken()));
    setAuthResolved(true);
  }, []);

  return { authResolved, hasToken };
}
