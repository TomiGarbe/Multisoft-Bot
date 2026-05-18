import { AlertCircle, Lock, LogIn, Mail } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { getToken, login } from '@/services/auth';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    if (getToken()) {
      router.replace('/dashboard');
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      router.replace('/dashboard');
    } catch (err: unknown) {
      const errorWithResponse = err as { response?: { data?: { detail?: string } } };
      const message = errorWithResponse.response?.data?.detail || 'No se pudo iniciar sesion';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-slate-50">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-gradient-to-br from-sky-50 via-white to-slate-100"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-sky-200/40 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -right-32 -bottom-32 h-96 w-96 rounded-full bg-indigo-200/40 blur-3xl"
      />

      <div className="relative mx-auto flex min-h-screen w-full max-w-md items-center justify-center px-4 py-8 sm:px-6">
        <div className="animate-modal w-full overflow-hidden rounded-2xl border border-slate-200 bg-white/95 p-8 shadow-xl ring-1 ring-black/5 backdrop-blur-sm">
          <div className="mb-7 text-center">
            <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-500 to-sky-700 text-xl font-bold text-white shadow-lg shadow-sky-200">
              M
            </span>
            <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">Bienvenido</h1>
            <p className="mt-1 text-sm text-slate-500">Ingresa a la plataforma de gestion.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email"
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@empresa.com"
              leadingIcon={<Mail />}
              autoComplete="email"
              required
            />

            <Input
              label="Contrasena"
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="********"
              leadingIcon={<Lock />}
              autoComplete="current-password"
              required
            />

            {error ? (
              <div className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            ) : null}

            <Button
              type="submit"
              loading={loading}
              leadingIcon={<LogIn />}
              className="w-full"
              size="lg"
            >
              {loading ? 'Ingresando...' : 'Ingresar'}
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-slate-400">
            Multisoft Bot - Plataforma de gestion
          </p>
        </div>
      </div>
    </div>
  );
}
