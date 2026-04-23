'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
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
    <div className="min-h-screen bg-slate-100 px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-md items-center">
        <div className="w-full rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-8 text-center">
            <span className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-600 text-xl font-bold text-white">
              M
            </span>
            <h1 className="mt-4 text-2xl font-bold text-slate-900">Multisoft Bot</h1>
            <p className="mt-1 text-sm text-slate-500">Inicia sesion para continuar</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <label htmlFor="email" className="text-sm font-medium text-slate-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@empresa.com"
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                required
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="password" className="text-sm font-medium text-slate-700">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="********"
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-slate-900 placeholder:text-slate-400 focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200"
                required
              />
            </div>

            {!!error && (
              <p className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-sky-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Ingresando...' : 'Ingresar'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
