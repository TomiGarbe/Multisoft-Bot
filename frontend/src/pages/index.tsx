import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { getToken } from '@/services/auth';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      router.replace('/dashboard');
    } else {
      router.replace('/login');
    }
  }, [router]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50">
      <div className="text-center">
        <h1 className="mb-4 text-3xl font-bold text-slate-900">Inicio</h1>
        <p className="text-slate-600">Redirigiendo a la sección correspondiente.</p>
      </div>
    </div>
  );
}
