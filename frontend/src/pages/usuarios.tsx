import { useEffect } from 'react';
import { useRouter } from 'next/router';

export default function UsuariosLegacyPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/admin/users');
  }, [router]);

  return null;
}
