'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppLayout from '@/components/layout/AppLayout';
import StatCard from '@/components/ui/StatCard';
import { getToken } from '@/services/auth';

export default function DashboardPage() {
  const router = useRouter();
  const hasToken = Boolean(getToken());

  const stats = [
    { title: 'Conversaciones', value: '120', subtitle: 'Total del periodo actual' },
    { title: 'Usuarios activos', value: '45', subtitle: 'Activos en las ultimas 24h' },
    { title: 'Mensajes enviados', value: '980', subtitle: 'Procesados este mes' },
    { title: 'Uso de tokens', value: '25k', subtitle: 'Consumo acumulado' },
  ];

  const recentActivity = [
    'Nuevo usuario creado',
    'Conversacion iniciada',
    'Mensaje enviado',
    'Flujo actualizado',
    'Sesion cerrada por inactividad',
  ];

  useEffect(() => {
    if (!hasToken) {
      router.replace('/login');
    }
  }, [hasToken, router]);

  if (!hasToken) {
    return null;
  }

  return (
    <AppLayout>
      <div className="space-y-8 p-6 md:p-8">
        <section>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Dashboard</h1>
          <p className="mt-2 text-sm text-slate-600">
            Vista general del rendimiento y actividad reciente del sistema.
          </p>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <StatCard key={stat.title} title={stat.title} value={stat.value} subtitle={stat.subtitle} />
          ))}
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Actividad reciente</h2>
          <p className="mt-1 text-sm text-slate-500">
            Eventos principales registrados recientemente en la plataforma.
          </p>

          <ul className="mt-5 space-y-3">
            {recentActivity.map((item) => (
              <li
                key={item}
                className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700"
              >
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </AppLayout>
  );
}
