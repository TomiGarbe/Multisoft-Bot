import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function UsuariosLegacyPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/users');
  }, [router]);

  return null;
}

