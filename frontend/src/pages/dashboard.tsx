import { useEffect, useMemo, useState } from 'react';
import { Coins, Globe, LayoutDashboard, UserPlus, Users } from 'lucide-react';
import { useRouter } from 'next/router';
import AppLayout from '@/components/layout/AppLayout';
import Button from '@/components/ui/Button';
import PageHeader from '@/components/ui/PageHeader';
import StatCard from '@/components/ui/StatCard';
import { useAuthToken } from '@/hooks/useAuthToken';
import { useTenantContext } from '@/context/tenant-context';
import ChannelDistributionChart from '@/dashboard/components/ChannelDistributionChart';
import ChartCard from '@/dashboard/components/ChartCard';
import ContactsByTypeGrid from '@/dashboard/components/ContactsByTypeGrid';
import ConversionFlowList from '@/dashboard/components/ConversionFlowList';
import DashboardSection from '@/dashboard/components/DashboardSection';
import EmptyState from '@/dashboard/components/EmptyState';
import ErrorState from '@/dashboard/components/ErrorState';
import LoadingState from '@/dashboard/components/LoadingState';
import TenantTokenRanking from '@/dashboard/components/TenantTokenRanking';
import UsageSeriesChart from '@/dashboard/components/UsageSeriesChart';
import { useDashboardData } from '@/dashboard/hooks/useDashboardData';
import type { DashboardScope } from '@/dashboard/types';

function isSuperAdmin(userType?: string, isBackdoor?: boolean): boolean {
  return userType === 'Backdoor' || isBackdoor === true;
}

export default function DashboardPage() {
  const hydrationDebugEnabled = process.env.NEXT_PUBLIC_DEBUG_HYDRATION === '1';
  const router = useRouter();
  const { authResolved, hasToken } = useAuthToken();
  const { user } = useTenantContext();
  const canUseGlobalScope = isSuperAdmin(user?.user_type, user?.is_backdoor);
  const [dashboardScope, setDashboardScope] = useState<DashboardScope>('tenant');
  const { data, loading, error, retry } = useDashboardData(
    dashboardScope,
    canUseGlobalScope,
    authResolved && hasToken,
  );

  useEffect(() => {
    if (!hydrationDebugEnabled) return;
    console.info('[RENDER] Dashboard', { authResolved, hasToken, dashboardScope, canUseGlobalScope });
  }, [hydrationDebugEnabled, authResolved, hasToken, dashboardScope, canUseGlobalScope]);

  useEffect(() => {
    if (!authResolved) return;
    if (!hasToken) {
      router.replace('/login');
    }
  }, [authResolved, hasToken, router]);

  useEffect(() => {
    if (!canUseGlobalScope && dashboardScope === 'global') {
      setDashboardScope('tenant');
    }
  }, [canUseGlobalScope, dashboardScope]);

  const topRowItems = useMemo(() => {
    if (!data) return [];
    return [
      {
        title: 'Usuarios totales',
        value: data.contacts.total.toLocaleString('es-AR'),
        subtitle: 'Base historica del tenant actual',
        icon: <Users className="h-5 w-5" />,
      },
      {
        title: 'Nuevos del mes',
        value: data.contacts.newThisMonth.toLocaleString('es-AR'),
        subtitle: 'Altas desde el inicio del mes',
        icon: <UserPlus className="h-5 w-5" />,
      },
      {
        title: 'Tokens consumidos',
        value: data.totalTokens.toLocaleString('es-AR'),
        subtitle: 'Consumo acumulado',
        icon: <Coins className="h-5 w-5" />,
      },
    ];
  }, [data]);

  if (!authResolved) {
    return <div className="min-h-screen bg-slate-50" />;
  }

  if (!hasToken) {
    return null;
  }

  return (
    <AppLayout>
      <div className="mx-auto w-full max-w-[1400px] space-y-6 p-4 sm:p-6 lg:space-y-8 lg:p-8">
        <PageHeader
          icon={<LayoutDashboard className="h-6 w-6" />}
          title="Dashboard operativo"
          description="Metricas en tiempo real para seguimiento de negocio y operaciones."
          actions={
            canUseGlobalScope ? (
              <Button
                variant={dashboardScope === 'global' ? 'primary' : 'secondary'}
                size="sm"
                leadingIcon={<Globe />}
                onClick={() =>
                  setDashboardScope((prev) => (prev === 'global' ? 'tenant' : 'global'))
                }
                title="Alternar vista del dashboard"
              >
                {dashboardScope === 'global' ? 'Vista global' : 'Vista tenant'}
              </Button>
            ) : null
          }
        />

        {loading ? <LoadingState cards={3} /> : null}

        {!loading && error ? <ErrorState message={error} onRetry={() => void retry()} /> : null}

        {!loading && !error && data ? (
          <div className="space-y-5 lg:space-y-6">
            <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {topRowItems.map((item) => (
                <StatCard
                  key={item.title}
                  title={item.title}
                  value={item.value}
                  subtitle={item.subtitle}
                  icon={item.icon}
                />
              ))}
            </section>

            {data.scope === 'tenant' ? (
              <DashboardSection
                title="Usuarios por tipo"
                description="Distribucion historica y crecimiento mensual por tipo de usuario/contacto."
              >
                <ContactsByTypeGrid items={data.contactsByType} />
              </DashboardSection>
            ) : null}

            {data.scope === 'tenant' ? (
              <DashboardSection
                title="Conversiones"
                description="Flujos de conversion entre tipos de usuario."
              >
                <ConversionFlowList items={data.conversions} />
              </DashboardSection>
            ) : null}

            <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
              <ChartCard
                title="Consumo de tokens por dia"
                description="Serie diaria de uso para el alcance actual."
              >
                <UsageSeriesChart data={data.usageSeries} />
              </ChartCard>

              {data.scope === 'tenant' ? (
                <ChartCard
                  title="Consumo por canal"
                  description="Distribucion de tokens por canal en este tenant."
                >
                  <ChannelDistributionChart data={data.tokensByChannel} />
                </ChartCard>
              ) : (
                <ChartCard
                  title="Consumo por negocio"
                  description="Ranking de tenants por consumo total de tokens."
                >
                  <TenantTokenRanking items={data.tokensByTenant} />
                </ChartCard>
              )}
            </div>

            <DashboardSection
              title="Notas operativas"
              description="Limitaciones o consideraciones del calculo de metricas."
            >
              {data.notes.length > 0 ? (
                <ul className="space-y-2 text-sm text-slate-600">
                  {data.notes.map((item) => (
                    <li
                      key={item}
                      className="rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-2"
                    >
                      {item}
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  title="Sin observaciones"
                  description="Todas las metricas cargaron correctamente para el alcance seleccionado."
                />
              )}
            </DashboardSection>
          </div>
        ) : null}
      </div>
    </AppLayout>
  );
}
